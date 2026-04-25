from django.db import migrations


def seed_catalog_data(apps, schema_editor):
    Category = apps.get_model("shop", "Category")
    Product = apps.get_model("shop", "Product")
    ProductVariant = apps.get_model("shop", "ProductVariant")

    categories = [
        ("Сумки", "sumki", 1),
        ("Кошельки", "koshelki", 2),
        ("Украшения", "ukrasheniya", 3),
        ("Ремни", "remni", 4),
        ("Браслеты", "braslety", 5),
        ("Брелоки", "breloki", 6),
    ]
    category_map = {}
    for name, slug, sort_order in categories:
        category, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "sort_order": sort_order, "is_active": True},
        )
        category_map[slug] = category

    products = [
        {
            "slug": "sumka-autumn",
            "name": "Сумка кожаная Autumn",
            "category_slug": "sumki",
            "material": "Натуральная кожа · Персонализация",
            "price": "4900.00",
            "badge": "hit",
            "badge_text": "ХИТ",
            "reviews_count": 34,
            "card_color_class": "pi-c1",
            "variants": [("#C8AA8A", "Песочный", True), ("#6B3A2A", "Tiramisu", False), ("#1A1A1A", "Черный", False)],
        },
        {
            "slug": "koshelek-gravirovka",
            "name": "Кошелек с гравировкой",
            "category_slug": "koshelki",
            "material": "Замша · Гравировка имени",
            "price": "1800.00",
            "badge": "new",
            "badge_text": "НОВИНКА",
            "reviews_count": 18,
            "card_color_class": "pi-c2",
            "variants": [("#D8C8A8", "Бежевый", True), ("#8A5A3A", "Коричневый", False)],
        },
        {
            "slug": "braslet-boheme",
            "name": "Браслет плетеный Boheme",
            "category_slug": "braslety",
            "material": "Текстиль + металл",
            "price": "760.00",
            "old_price": "950.00",
            "badge": "sale",
            "badge_text": "-20%",
            "reviews_count": 42,
            "card_color_class": "pi-c3",
            "variants": [("#E0D0B8", "Кремовый", True), ("#7A4A30", "Каштан", False)],
        },
        {
            "slug": "remen-handmade",
            "name": "Ремень ручной работы",
            "category_slug": "remni",
            "material": "Кожа растительного дубления",
            "price": "2400.00",
            "badge": "none",
            "reviews_count": 11,
            "card_color_class": "pi-c4",
            "variants": [("#C8B898", "Тан", True), ("#6B3A2A", "Tiramisu", False)],
        },
    ]

    for item in products:
        product, _ = Product.objects.get_or_create(
            slug=item["slug"],
            defaults={
                "name": item["name"],
                "category": category_map[item["category_slug"]],
                "material": item["material"],
                "price": item["price"],
                "old_price": item.get("old_price"),
                "reviews_count": item["reviews_count"],
                "badge": item["badge"],
                "badge_text": item.get("badge_text", ""),
                "card_color_class": item["card_color_class"],
                "is_active": True,
            },
        )
        for color_hex, color_name, is_default in item["variants"]:
            ProductVariant.objects.get_or_create(
                product=product,
                color_hex=color_hex,
                defaults={"color_name": color_name, "is_default": is_default, "stock": 50},
            )


def rollback_seed_data(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    Product.objects.filter(
        slug__in=[
            "sumka-autumn",
            "koshelek-gravirovka",
            "braslet-boheme",
            "remen-handmade",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("shop", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_catalog_data, rollback_seed_data),
    ]
