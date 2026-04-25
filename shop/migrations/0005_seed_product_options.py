from django.db import migrations


def seed_product_options(apps, schema_editor):
    Product = apps.get_model("shop", "Product")
    Product.objects.filter(slug__in=["koshelek-gravirovka", "kolco-noor", "brelok-monogram"]).update(has_engraving=True)
    Product.objects.filter(slug__in=["sumka-autumn", "sumka-sand-wave", "clutch-dusk"]).update(has_gift_wrap=True)


class Migration(migrations.Migration):
    dependencies = [
        ("shop", "0004_order_product_has_engraving_product_has_gift_wrap_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_product_options, migrations.RunPython.noop),
    ]
