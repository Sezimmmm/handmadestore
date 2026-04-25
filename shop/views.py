import json
import uuid
from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from urllib.parse import urlencode

from .constants import BUILDER_PRODUCT_SLUG, CUSTOM_PERSONAL_PRODUCT_PREFIX, SESSION_BUILDER_CART_KEY
from .models import Category, Order, OrderItem, Product, ProductImage, ProductVariant

CART_VARIANT_SEP = "::v"

PERSONALIZATION_BASE_BY_SHAPE = {
    "bag": Decimal("4900"),
    "wallet": Decimal("1800"),
    "bracelet": Decimal("950"),
    "belt": Decimal("2400"),
    "keychain": Decimal("680"),
    "cover": Decimal("1200"),
}
PERSONALIZATION_MATERIAL_EXTRA = {
    "Натуральная кожа": Decimal("500"),
    "Замша": Decimal("300"),
    "Растительное дубление": Decimal("0"),
    "Комбинированный": Decimal("0"),
    "Металл + кожа": Decimal("700"),
    "Текстиль": Decimal("0"),
}
PERSONALIZATION_EXTRA_PRICES = {
    "Подарочная упаковка": Decimal("350"),
    "Открытка с пожеланием": Decimal("150"),
    "Срочное изготовление": Decimal("500"),
    "Лента и монограмма": Decimal("200"),
}
PERSONALIZATION_ENGRAVING_FEE = Decimal("400")
PERSONALIZATION_ALLOWED_FONTS = frozenset({"serif", "sans-serif", "cursive"})


def _get_builder_cart(request):
    raw = request.session.get(SESSION_BUILDER_CART_KEY)
    if not isinstance(raw, list):
        return []
    return raw


def _builder_product():
    return Product.objects.filter(
        slug=BUILDER_PRODUCT_SLUG,
        is_active=True,
        category__is_active=True,
    ).select_related("category").first()


def _ensure_builder_product():
    """Return active builder catalog row; create/repair if missing."""
    category = Category.objects.filter(is_active=True).order_by("sort_order", "id").first()
    if category is None:
        return None
    p, _ = Product.objects.get_or_create(
        slug=BUILDER_PRODUCT_SLUG,
        defaults={
            "name": "Индивидуальный заказ (конструктор)",
            "category": category,
            "material": "Параметры в заметке к позиции заказа",
            "description": "Изделие из онлайн-конструктора персонализации.",
            "price": Decimal("0.00"),
            "is_personalizable": False,
            "has_engraving": False,
            "has_gift_wrap": False,
            "is_active": True,
            "badge": Product.BADGE_NONE,
        },
    )
    changed = False
    if not p.is_active:
        p.is_active = True
        changed = True
    if not p.category_id or not p.category.is_active:
        p.category = category
        changed = True
    if changed:
        p.save(update_fields=["is_active", "category"])
    return Product.objects.filter(pk=p.pk).select_related("category").first()


def _normalize_personalization_payload(data: dict) -> tuple[dict | None, str | None]:
    """Validate and normalize client JSON. Returns (config, error_message)."""
    if not isinstance(data, dict):
        return None, "invalid_payload"
    shape = (data.get("productShape") or "").strip()
    if shape not in PERSONALIZATION_BASE_BY_SHAPE:
        return None, "invalid_shape"
    material = (data.get("material") or "").strip()
    if material not in PERSONALIZATION_MATERIAL_EXTRA:
        return None, "invalid_material"
    color_hex = (data.get("color") or "").strip()
    if len(color_hex) > 16:
        return None, "invalid_color"
    color_name = (data.get("colorName") or "").strip()[:120]
    fitting = (data.get("fitting") or "").strip()[:80]
    eng1 = (data.get("engraving") or "").strip()[:20]
    eng2 = (data.get("engravingLine2") or "").strip()[:20]
    font = (data.get("engravingFont") or "serif").strip()
    if font not in PERSONALIZATION_ALLOWED_FONTS:
        font = "serif"
    placement = (data.get("engravingPlacement") or "По центру").strip()[:40]
    product_name = (data.get("product") or "").strip()[:180]
    extras_in = data.get("extras")
    if extras_in is None:
        extras_in = []
    if not isinstance(extras_in, list):
        return None, "invalid_extras"
    extras_out = []
    seen = set()
    for row in extras_in:
        if not isinstance(row, dict):
            continue
        name = (row.get("name") or "").strip()
        if not name or name in seen:
            continue
        price_allowed = PERSONALIZATION_EXTRA_PRICES.get(name)
        if price_allowed is None:
            return None, "invalid_extra"
        extras_out.append({"name": name, "price": str(price_allowed)})
        seen.add(name)
    base = PERSONALIZATION_BASE_BY_SHAPE[shape]
    mat_extra = PERSONALIZATION_MATERIAL_EXTRA[material]
    eng_fee = PERSONALIZATION_ENGRAVING_FEE if (eng1 or eng2) else Decimal("0")
    extras_total = sum(PERSONALIZATION_EXTRA_PRICES[e["name"]] for e in extras_out)
    total = base + mat_extra + eng_fee + extras_total
    config = {
        "product_shape": shape,
        "product_name": product_name,
        "material": material,
        "color_hex": color_hex,
        "color_name": color_name,
        "fitting": fitting,
        "engraving": eng1,
        "engraving_line2": eng2,
        "engraving_font": font,
        "engraving_placement": placement,
        "extras": extras_out,
        "total_kgs": str(total),
    }
    return config, None


def _personalization_total_from_config(config: dict) -> Decimal:
    shape = config["product_shape"]
    base = PERSONALIZATION_BASE_BY_SHAPE[shape]
    mat_extra = PERSONALIZATION_MATERIAL_EXTRA[config["material"]]
    eng_fee = PERSONALIZATION_ENGRAVING_FEE if (config.get("engraving") or config.get("engraving_line2")) else Decimal("0")
    extras_total = Decimal("0")
    for row in config.get("extras") or []:
        extras_total += PERSONALIZATION_EXTRA_PRICES[row["name"]]
    return base + mat_extra + eng_fee + extras_total


def _builder_summary_lines(config: dict) -> list[str]:
    lines = [
        f"{config.get('product_name') or config['product_shape']}",
        f"{config['material']}",
    ]
    if config.get("color_name") or config.get("color_hex"):
        lines.append(f"{config.get('color_name', '')} {config.get('color_hex', '')}".strip())
    if config.get("fitting"):
        lines.append(_("Fitting: %(name)s") % {"name": config["fitting"]})
    eng = " ".join(
        x for x in (config.get("engraving") or "", config.get("engraving_line2") or "") if x
    ).strip()
    if eng:
        lines.append(_("Engraving: %(text)s") % {"text": eng})
    for row in config.get("extras") or []:
        lines.append(row["name"])
    return [ln for ln in lines if ln]


def _cart_line_key(slug: str, variant_id: int | None) -> str:
    if variant_id:
        return f"{slug}{CART_VARIANT_SEP}{variant_id}"
    return slug


def _parse_cart_line_key(key: str) -> tuple[str, int | None]:
    if CART_VARIANT_SEP in key:
        slug, _, rest = key.partition(CART_VARIANT_SEP)
        if rest.isdigit():
            return slug, int(rest)
        return slug, None
    return key, None


def _cart_qty_value(raw) -> int:
    if isinstance(raw, bool):
        return 0
    if isinstance(raw, int):
        return max(0, raw)
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return 0


def _cart_lines_bundle(request):
    """Resolve session cart into display rows and total. Skips unknown products or stale variant ids."""
    cart = _get_cart(request)
    parsed = []
    for key, raw_qty in cart.items():
        qty = _cart_qty_value(raw_qty)
        if qty < 1:
            continue
        slug, variant_id = _parse_cart_line_key(key)
        if slug == BUILDER_PRODUCT_SLUG:
            continue
        parsed.append((slug, variant_id, qty))
    items = []
    total = Decimal("0")
    if parsed:
        slugs = {slug for slug, _, _ in parsed}
        products = (
            Product.objects.filter(slug__in=slugs, is_active=True, category__is_active=True)
            .select_related("category")
            .prefetch_related(
                Prefetch("variants", ProductVariant.objects.order_by("id")),
            )
        )
        pmap = {p.slug: p for p in products}
        for slug, variant_id, qty in parsed:
            product = pmap.get(slug)
            if not product:
                continue
            variant = None
            if variant_id is not None:
                variant = next((v for v in product.variants.all() if v.id == variant_id), None)
                if variant is None:
                    continue
            subtotal = product.price * qty
            total += subtotal
            items.append(
                {
                    "product": product,
                    "variant": variant,
                    "quantity": qty,
                    "subtotal": subtotal,
                    "is_builder": False,
                }
            )
    builder_product = _ensure_builder_product()
    cart_keys = set(cart.keys())
    for entry in _get_builder_cart(request):
        if not isinstance(entry, dict):
            continue
        bid = (entry.get("id") or "").strip()
        cfg = entry.get("config")
        if not bid or not isinstance(cfg, dict):
            continue
        linked_slug = (entry.get("linked_slug") or "").strip()
        if linked_slug and linked_slug in cart_keys:
            # Standard cart row already exists for this personalization item.
            continue
        try:
            line_total = Decimal(str(entry.get("total") or "0"))
        except Exception:
            line_total = _personalization_total_from_config(cfg)
        if line_total <= 0:
            continue
        product_for_row = builder_product or {
            "name": _("Custom accessory"),
            "material": _("Personalization configuration"),
            "category": {"name": _("Personalization")},
            "price": line_total,
            "slug": BUILDER_PRODUCT_SLUG,
        }
        items.append(
            {
                "product": product_for_row,
                "variant": None,
                "quantity": 1,
                "subtotal": line_total,
                "unit_price": line_total,
                "is_builder": True,
                "builder_id": bid,
                "builder_config": cfg,
                "builder_lines": _builder_summary_lines(cfg),
            }
        )
        total += line_total
    return items, total


def _variant_image_rows(product):
    images = list(product.images.all())

    def first_image_url():
        for im in images:
            if im.image:
                return im.image.url
        return ""

    def url_for_variant(variant_id):
        for im in images:
            if im.variant_id == variant_id and im.image:
                return im.image.url
        for im in images:
            if im.variant_id is None and im.image:
                return im.image.url
        return ""

    fallback = first_image_url()
    rows = []
    for v in product.variants.all():
        u = url_for_variant(v.id) or fallback
        rows.append(
            {
                "id": v.id,
                "name": v.color_name,
                "hex": v.color_hex,
                "url": u,
                "default": v.is_default,
            }
        )
    primary = next((r for r in rows if r["default"]), rows[0] if rows else None)
    primary_url = (primary or {}).get("url") or fallback
    return rows, primary_url


def _get_cart(request):
    return request.session.setdefault("cart", {})


def _cart_count(request):
    cart = _get_cart(request)
    n = sum(
        _cart_qty_value(v)
        for k, v in cart.items()
        if _parse_cart_line_key(k)[0] != BUILDER_PRODUCT_SLUG
    )
    cart_keys = set(cart.keys())
    mirrored = 0
    for entry in _get_builder_cart(request):
        if not isinstance(entry, dict):
            continue
        linked_slug = (entry.get("linked_slug") or "").strip()
        if linked_slug and linked_slug in cart_keys:
            continue
        mirrored += 1
    n += mirrored
    return n


def home(request):
    categories = Category.objects.filter(is_active=True).order_by("sort_order", "name")
    category_counts_qs = (
        Product.objects.filter(is_active=True, category__is_active=True)
        .exclude(slug=BUILDER_PRODUCT_SLUG)
        .exclude(slug__startswith=CUSTOM_PERSONAL_PRODUCT_PREFIX)
        .values_list("category__slug", flat=True)
    )
    category_counts = {}
    for slug in category_counts_qs:
        category_counts[slug] = category_counts.get(slug, 0) + 1
    home_categories = [
        {"slug": category.slug, "name": category.name, "count": category_counts.get(category.slug, 0)}
        for category in categories[:6]
    ]
    return render(request, "shop/home.html", {"home_categories": home_categories})


def account(request):
    return render(request, "shop/account.html")


def catalog(request):
    base_products_qs = (
        Product.objects.filter(is_active=True, category__is_active=True)
        .exclude(slug=BUILDER_PRODUCT_SLUG)
        .exclude(slug__startswith=CUSTOM_PERSONAL_PRODUCT_PREFIX)
        .select_related("category")
        .prefetch_related("variants")
    )
    products_qs = base_products_qs
    selected_category = request.GET.get("category", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    search_query = request.GET.get("q", "").strip()
    selected_sort = request.GET.get("sort", "popular")
    selected_materials = request.GET.getlist("material")
    selected_colors = request.GET.getlist("color")
    only_personalizable = request.GET.get("only_personalizable") == "1"
    only_engraving = request.GET.get("only_engraving") == "1"
    only_gift_wrap = request.GET.get("only_gift_wrap") == "1"
    only_hits = request.GET.get("only_hits") == "1"

    if selected_category:
        products_qs = products_qs.filter(category__slug=selected_category)
    if min_price and min_price.isdigit():
        products_qs = products_qs.filter(price__gte=min_price)
    if max_price and max_price.isdigit():
        products_qs = products_qs.filter(price__lte=max_price)
    if search_query:
        products_qs = products_qs.filter(Q(name__icontains=search_query) | Q(material__icontains=search_query))
    if selected_materials:
        for material in selected_materials:
            products_qs = products_qs.filter(material__icontains=material)
    if selected_colors:
        products_qs = products_qs.filter(variants__color_hex__in=selected_colors)
    if only_personalizable:
        products_qs = products_qs.filter(is_personalizable=True)
    if only_engraving:
        products_qs = products_qs.filter(has_engraving=True)
    if only_gift_wrap:
        products_qs = products_qs.filter(has_gift_wrap=True)
    if only_hits:
        products_qs = products_qs.filter(badge=Product.BADGE_HIT)

    sort_map = {
        "popular": "-reviews_count",
        "cheap": "price",
        "expensive": "-price",
        "newest": "-created_at",
        "rating": "-rating",
    }
    products_qs = products_qs.order_by(sort_map.get(selected_sort, "-reviews_count")).distinct()

    paginator = Paginator(products_qs, 6)
    page_obj = paginator.get_page(request.GET.get("page"))
    categories = Category.objects.filter(is_active=True).order_by("sort_order", "name")
    material_choices = ["Натуральная кожа", "Замша", "Текстиль", "Металл", "Комбинированный"]
    color_choices = [
        {"name": "Бежевый", "hex": "#C8AA8A"},
        {"name": "Коричневый", "hex": "#6B3A2A"},
        {"name": "Кремовый", "hex": "#F0EBE0"},
        {"name": "Черный", "hex": "#1A1A1A"},
        {"name": "Песочный", "hex": "#D8C8A8"},
        {"name": "Терракота", "hex": "#B86A4A"},
        {"name": "Винный", "hex": "#6A2A30"},
        {"name": "Оливковый", "hex": "#6A7040"},
        {"name": "Графит", "hex": "#4A4A52"},
        {"name": "Синий", "hex": "#2A4A70"},
        {"name": "Бирюзовый", "hex": "#2A6A6A"},
        {"name": "Золотой", "hex": "#C8A860"},
        {"name": "Серый", "hex": "#9A9A9A"},
        {"name": "Белый", "hex": "#FFFFFF"},
        {"name": "Темно-коричневый", "hex": "#3A2010"},
    ]
    query_params = request.GET.copy()
    query_params.pop("page", None)
    query_string = query_params.urlencode()
    category_counts_qs = (
        Product.objects.filter(is_active=True, category__is_active=True)
        .exclude(slug=BUILDER_PRODUCT_SLUG)
        .exclude(slug__startswith=CUSTOM_PERSONAL_PRODUCT_PREFIX)
        .values_list("category__slug", flat=True)
    )
    category_counts = {}
    for slug in category_counts_qs:
        category_counts[slug] = category_counts.get(slug, 0) + 1
    categories_with_counts = [
        {"slug": category.slug, "name": category.name, "count": category_counts.get(category.slug, 0)}
        for category in categories
    ]

    active_filters = []

    def build_query_without(key, value=None):
        mutable = request.GET.copy()
        if value is None:
            mutable.pop(key, None)
        else:
            values = mutable.getlist(key)
            values = [v for v in values if v != value]
            mutable.setlist(key, values)
        mutable.pop("page", None)
        encoded = urlencode([(k, v) for k in mutable for v in mutable.getlist(k)])
        return f"{reverse('catalog')}?{encoded}" if encoded else reverse("catalog")

    if selected_category:
        category_name = next((cat.name for cat in categories if cat.slug == selected_category), selected_category)
        active_filters.append(
            {"label": _("Category: %(name)s") % {"name": category_name}, "remove_url": build_query_without("category")}
        )
    if min_price:
        active_filters.append(
            {"label": _("Min price: %(value)s") % {"value": min_price}, "remove_url": build_query_without("min_price")}
        )
    if max_price:
        active_filters.append(
            {"label": _("Max price: %(value)s") % {"value": max_price}, "remove_url": build_query_without("max_price")}
        )
    for material in selected_materials:
        active_filters.append(
            {"label": _("Material: %(name)s") % {"name": material}, "remove_url": build_query_without("material", material)}
        )
    for color in selected_colors:
        color_name = next((item["name"] for item in color_choices if item["hex"] == color), color)
        active_filters.append(
            {"label": _("Color: %(name)s") % {"name": color_name}, "remove_url": build_query_without("color", color)}
        )
    if only_personalizable:
        active_filters.append({"label": _("Personalization"), "remove_url": build_query_without("only_personalizable")})
    if only_engraving:
        active_filters.append({"label": _("Engraving"), "remove_url": build_query_without("only_engraving")})
    if only_gift_wrap:
        active_filters.append({"label": _("Gift packaging"), "remove_url": build_query_without("only_gift_wrap")})
    if only_hits:
        active_filters.append({"label": _("Hits only"), "remove_url": build_query_without("only_hits")})

    context = {
        "products": page_obj.object_list,
        "products_count": products_qs.count(),
        "total_products_count": base_products_qs.count(),
        "page_obj": page_obj,
        "cart_count": _cart_count(request),
        "categories": categories,
        "selected_category": selected_category,
        "selected_sort": selected_sort,
        "selected_materials": selected_materials,
        "selected_colors": selected_colors,
        "min_price": min_price,
        "max_price": max_price,
        "only_personalizable": only_personalizable,
        "only_engraving": only_engraving,
        "only_gift_wrap": only_gift_wrap,
        "only_hits": only_hits,
        "material_choices": material_choices,
        "color_choices": color_choices,
        "query_string": query_string,
        "active_filters": active_filters,
        "categories_with_counts": categories_with_counts,
        "search_query": search_query,
    }
    return render(request, "shop/catalog.html", context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.filter(is_active=True, category__is_active=True)
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "variants",
                ProductVariant.objects.order_by("-is_default", "id"),
            ),
            Prefetch(
                "images",
                ProductImage.objects.select_related("variant").order_by("-is_primary", "id"),
            ),
        ),
        slug=slug,
    )
    if product.slug == BUILDER_PRODUCT_SLUG or product.slug.startswith(CUSTOM_PERSONAL_PRODUCT_PREFIX):
        raise Http404()
    related_products = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(id=product.id)
        .order_by("-created_at")[:4]
    )
    variant_rows, primary_image_url = _variant_image_rows(product)
    default_variant_name = ""
    default_variant_id = None
    if variant_rows:
        default_row = next((r for r in variant_rows if r["default"]), variant_rows[0])
        default_variant_name = default_row["name"]
        default_variant_id = default_row.get("id")
    context = {
        "product": product,
        "related_products": related_products,
        "cart_count": _cart_count(request),
        "variant_rows": variant_rows,
        "primary_product_image_url": primary_image_url,
        "default_variant_name": default_variant_name,
        "default_variant_id": default_variant_id,
    }
    return render(request, "shop/product_detail.html", context)


def cart_detail(request):
    cart_items, total = _cart_lines_bundle(request)
    context = {
        "cart_items": cart_items,
        "cart_count": _cart_count(request),
        "cart_total": total,
    }
    return render(request, "shop/cart.html", context)


def checkout(request):
    cart_items, total = _cart_lines_bundle(request)

    if request.method == "POST" and cart_items:
        builder_product = _ensure_builder_product()
        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        email = request.POST.get("email", "").strip()
        comment = request.POST.get("comment", "").strip()
        if full_name and phone and address:
            order = Order.objects.create(
                full_name=full_name,
                phone=phone,
                address=address,
                email=email,
                comment=comment,
                total_amount=total,
            )
            for item in cart_items:
                product_obj = item["product"]
                if item.get("is_builder") and not isinstance(product_obj, Product):
                    if builder_product is None:
                        continue
                    product_obj = builder_product
                unit_price = item.get("unit_price", item["product"].price)
                notes = ""
                if item.get("is_builder") and item.get("builder_config"):
                    notes = json.dumps(item["builder_config"], ensure_ascii=False)
                OrderItem.objects.create(
                    order=order,
                    product=product_obj,
                    variant=item["variant"],
                    quantity=item["quantity"],
                    unit_price=unit_price,
                    subtotal=item["subtotal"],
                    personalization_notes=notes,
                )
            request.session["cart"] = {}
            request.session[SESSION_BUILDER_CART_KEY] = []
            request.session.modified = True
            return redirect("checkout_success")

    return render(
        request,
        "shop/checkout.html",
        {"cart_items": cart_items, "cart_total": total, "cart_count": _cart_count(request)},
    )


def checkout_success(request):
    return render(request, "shop/checkout_success.html")


def cart_add(request, slug):
    if slug == BUILDER_PRODUCT_SLUG or slug.startswith(CUSTOM_PERSONAL_PRODUCT_PREFIX):
        raise Http404()
    product = get_object_or_404(Product, slug=slug, is_active=True, category__is_active=True)
    variant_id = None
    raw_variant = request.GET.get("variant", "").strip()
    if raw_variant.isdigit():
        vid = int(raw_variant)
        if product.variants.filter(pk=vid).exists():
            variant_id = vid
    key = _cart_line_key(product.slug, variant_id)
    cart = _get_cart(request)
    cart[key] = cart.get(key, 0) + 1
    request.session.modified = True
    return redirect(request.GET.get("next") or "cart_detail")


def cart_remove(request, slug):
    cart = _get_cart(request)
    raw_variant = request.GET.get("variant", "").strip()
    if raw_variant.isdigit():
        key = _cart_line_key(slug, int(raw_variant))
        cart.pop(key, None)
    else:
        cart.pop(slug, None)
    request.session.modified = True
    return redirect("cart_detail")


def cart_clear(request):
    request.session["cart"] = {}
    request.session[SESSION_BUILDER_CART_KEY] = []
    request.session.modified = True
    return redirect(request.GET.get("next") or "cart_detail")


def cart_remove_builder(request, builder_id: str):
    bid = (builder_id or "").strip()
    if not bid:
        return redirect("cart_detail")
    raw = _get_builder_cart(request)
    request.session[SESSION_BUILDER_CART_KEY] = [e for e in raw if isinstance(e, dict) and (e.get("id") or "") != bid]
    request.session.modified = True
    return redirect("cart_detail")


@require_POST
def personalization_add_to_cart(request):
    # Keep creating/repairing helper product for old session-cart compatibility.
    _ensure_builder_product()
    try:
        data = json.loads(request.body.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)
    config, err = _normalize_personalization_payload(data)
    if err or not config:
        return JsonResponse({"ok": False, "error": err or "invalid"}, status=400)
    total = _personalization_total_from_config(config)
    if str(total) != config.get("total_kgs"):
        config["total_kgs"] = str(total)
    category = Category.objects.filter(is_active=True).order_by("sort_order", "id").first()
    if category is None:
        return JsonResponse({"ok": False, "error": "no_active_category"}, status=503)
    pid = uuid.uuid4().hex
    product = Product.objects.create(
        category=category,
        name=f"Индивидуальный заказ #{pid[:8]}",
        slug=f"{CUSTOM_PERSONAL_PRODUCT_PREFIX}{pid}",
        material=config["material"],
        description=json.dumps(config, ensure_ascii=False),
        price=total,
        badge=Product.BADGE_NONE,
        is_personalizable=False,
        has_engraving=bool(config.get("engraving") or config.get("engraving_line2")),
        has_gift_wrap=any((e.get("name") == "Подарочная упаковка") for e in (config.get("extras") or [])),
        is_active=True,
    )
    cart = _get_cart(request)
    key = _cart_line_key(product.slug, None)
    cart[key] = _cart_qty_value(cart.get(key, 0)) + 1
    # Compatibility fallback: mirror config in builder_cart_items.
    # If regular cart line resolves, _cart_lines_bundle skips this mirrored row.
    lst = _get_builder_cart(request)
    lst.append(
        {
            "id": uuid.uuid4().hex,
            "total": str(total),
            "config": config,
            "linked_slug": product.slug,
        }
    )
    request.session[SESSION_BUILDER_CART_KEY] = lst
    request.session.modified = True
    return JsonResponse({"ok": True, "cart_count": _cart_count(request), "product_slug": product.slug})


def about(request):
    return render(request, "shop/about.html")


@ensure_csrf_cookie
def personalization(request):
    return render(
        request,
        "shop/personalization.html",
        {
            "personalization_add_url": reverse("personalization_add_to_cart"),
        },
    )


def contacts(request):
    return render(request, "shop/contacts.html")
