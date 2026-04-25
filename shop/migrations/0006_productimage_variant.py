import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0005_seed_product_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="productimage",
            name="variant",
            field=models.ForeignKey(
                blank=True,
                help_text="Если указан — фото для этого цвета/варианта. Пусто = общее фото товара.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="images",
                to="shop.productvariant",
            ),
        ),
    ]
