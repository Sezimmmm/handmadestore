from shop.constants import BUILDER_PRODUCT_SLUG, SESSION_BUILDER_CART_KEY


def cart_count(request):
    raw = request.session.get("cart") or {}
    if not isinstance(raw, dict):
        raw = {}
    n = 0
    for key, v in raw.items():
        slug = key.split("::v", 1)[0] if "::v" in key else key
        if slug == BUILDER_PRODUCT_SLUG:
            continue
        try:
            n += int(v)
        except (TypeError, ValueError):
            continue
    builders = request.session.get(SESSION_BUILDER_CART_KEY)
    if isinstance(builders, list):
        n += len(builders)
    return {"cart_count": n}
