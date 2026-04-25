from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    BADGE_NONE = "none"
    BADGE_HIT = "hit"
    BADGE_NEW = "new"
    BADGE_SALE = "sale"
    BADGE_CHOICES = [
        (BADGE_NONE, "Нет"),
        (BADGE_HIT, "Хит"),
        (BADGE_NEW, "Новинка"),
        (BADGE_SALE, "Скидка"),
    ]

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220, unique=True)
    material = models.CharField(max_length=180, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=5.0)
    reviews_count = models.PositiveIntegerField(default=0)
    badge = models.CharField(max_length=10, choices=BADGE_CHOICES, default=BADGE_NONE)
    badge_text = models.CharField(max_length=20, blank=True)
    card_color_class = models.CharField(max_length=20, default="pi-c1")
    is_personalizable = models.BooleanField(default=True)
    has_engraving = models.BooleanField(default=False)
    has_gift_wrap = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    color_name = models.CharField(max_length=60)
    color_hex = models.CharField(max_length=7, help_text="Например: #C8AA8A")
    is_default = models.BooleanField(default=False)
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=80, blank=True)

    class Meta:
        verbose_name = "Вариант товара"
        verbose_name_plural = "Варианты товара"

    def __str__(self):
        return f"{self.product.name} — {self.color_name}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    variant = models.ForeignKey(
        "ProductVariant",
        on_delete=models.CASCADE,
        related_name="images",
        null=True,
        blank=True,
        help_text="Если указан — фото для этого цвета/варианта. Пусто = общее фото товара.",
    )
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    alt = models.CharField(max_length=180, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Изображение товара"
        verbose_name_plural = "Изображения товара"

    def __str__(self):
        return f"Изображение: {self.product.name}"


class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_PROCESSING = "processing"
    STATUS_DONE = "done"
    STATUS_CHOICES = [
        (STATUS_NEW, "Новый"),
        (STATUS_PROCESSING, "В обработке"),
        (STATUS_DONE, "Завершен"),
    ]

    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255)
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ #{self.id} — {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="Цвет / вариант",
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    personalization_notes = models.TextField(
        blank=True,
        default="",
        verbose_name="Персонализация (JSON)",
        help_text="Для позиций из конструктора — параметры изделия в JSON.",
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        suffix = f" ({self.variant.color_name})" if self.variant_id else ""
        return f"{self.product.name}{suffix} x {self.quantity}"
