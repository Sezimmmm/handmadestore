from shop.constants import BUILDER_PRODUCT_SLUG, SESSION_BUILDER_CART_KEY


def cart_count(request):
    raw = request.session.get("cart") or {}
    if not isinstance(raw, dict):
        raw = {}
    cart_keys = set(raw.keys())
    n = 0
    for key, v in raw.items():
        slug = key.split("::v", 1)[0] if "::v" in key else key
        if slug == BUILDER_PRODUCT_SLUG:
            continue
        try:
            qty = int(v)
            if qty > 0:
                n += qty
        except (TypeError, ValueError):
            continue
    builders = request.session.get(SESSION_BUILDER_CART_KEY)
    if isinstance(builders, list):
        for entry in builders:
            if not isinstance(entry, dict):
                continue
            linked_slug = (entry.get("linked_slug") or "").strip()
            if linked_slug and linked_slug in cart_keys:
                continue
            n += 1
    return {"cart_count": n}
