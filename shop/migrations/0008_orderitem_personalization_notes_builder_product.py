from decimal import Decimal

from django.db import migrations, models


def create_builder_product(apps, schema_editor):
    Category = apps.get_model("shop", "Category")
    Product = apps.get_model("shop", "Product")
    category = Category.objects.order_by("sort_order", "id").first()
    if category is None:
        category = Category.objects.create(
            name="Каталог",
            slug="catalog-root",
            sort_order=0,
            is_active=True,
        )
    Product.objects.get_or_create(
        slug="maison-personalization-builder",
        defaults={
            "name": "Индивидуальный заказ (конструктор)",
            "category": category,
            "material": "Параметры в заметке к позиции заказа",
            "description": "Изделие, собранное в онлайн-конструкторе персонализации.",
            "price": Decimal("0.00"),
            "is_personalizable": False,
            "has_engraving": False,
            "has_gift_wrap": False,
            "is_active": True,
            "badge": "none",
        },
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("shop", "0007_orderitem_variant"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="personalization_notes",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Для позиций из конструктора — параметры изделия в JSON.",
                verbose_name="Персонализация (JSON)",
            ),
        ),
        migrations.RunPython(create_builder_product, noop_reverse),
    ]
