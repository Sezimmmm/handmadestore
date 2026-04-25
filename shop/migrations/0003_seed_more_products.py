from django.db import migrations


def seed_more_products(apps, schema_editor):
    Category = apps.get_model("shop", "Category")
    Product = apps.get_model("shop", "Product")
    ProductVariant = apps.get_model("shop", "ProductVariant")

    items = [
        ("ukrasheniya", "sergi-desert-moon", "Серьги Desert Moon", "Серебро + натуральный камень", "1530.00", "1800.00", "sale", "-15%", "pi-c8"),
        ("koshelki", "kartholder-slim", "Картхолдер Slim", "Натуральная кожа · 6 отделений", "1100.00", None, "none", "", "pi-c9"),
        ("sumki", "clutch-dusk", "Клатч Dusk", "Замша · Металлическая фурнитура", "3700.00", None, "none", "", "pi-c7"),
        ("breloki", "brelok-monogram", "Брелок Monogram", "Кожа · Персональные инициалы", "680.00", None, "new", "НОВИНКА", "pi-c6"),
        ("ukrasheniya", "kolco-noor", "Кольцо Noor", "Серебро 925 · Гравировка", "3200.00", None, "hit", "ХИТ", "pi-c5"),
        ("sumki", "sumka-sand-wave", "Сумка Sand Wave", "Кожа + текстиль", "4200.00", None, "none", "", "pi-c10"),
        ("remni", "remen-classic", "Ремень Classic", "Кожа растительного дубления", "2600.00", None, "none", "", "pi-c11"),
        ("braslety", "braslet-nomad", "Браслет Nomad", "Текстиль + латунь", "890.00", None, "new", "НОВИНКА", "pi-c12"),
    ]

    for category_slug, slug, name, material, price, old_price, badge, badge_text, card_color_class in items:
        category = Category.objects.filter(slug=category_slug).first()
        if not category:
            continue
        product, _ = Product.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "category": category,
                "material": material,
                "price": price,
                "old_price": old_price,
                "reviews_count": 10,
                "badge": badge,
                "badge_text": badge_text,
                "card_color_class": card_color_class,
                "is_active": True,
            },
        )
        ProductVariant.objects.get_or_create(
            product=product,
            color_hex="#C8AA8A",
            defaults={"color_name": "Песочный", "is_default": True, "stock": 50},
        )
        ProductVariant.objects.get_or_create(
            product=product,
            color_hex="#6B3A2A",
            defaults={"color_name": "Tiramisu", "is_default": False, "stock": 35},
        )


def rollback_more_products(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    Product.objects.filter(
        slug__in=[
            "sergi-desert-moon",
            "kartholder-slim",
            "clutch-dusk",
            "brelok-monogram",
            "kolco-noor",
            "sumka-sand-wave",
            "remen-classic",
            "braslet-nomad",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("shop", "0002_seed_catalog_data"),
    ]

    operations = [
        migrations.RunPython(seed_more_products, rollback_more_products),
    ]
