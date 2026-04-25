from django.contrib import admin

from .models import Category, Order, OrderItem, Product, ProductImage, ProductVariant


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("variant", "image", "alt", "is_primary")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "variant":
            parent = self.get_parent_object(request)
            if parent:
                kwargs["queryset"] = ProductVariant.objects.filter(product=parent).order_by(
                    "-is_default", "id"
                )
            else:
                kwargs["queryset"] = ProductVariant.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("sort_order", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "old_price", "badge", "is_active")
    list_filter = ("category", "badge", "is_active")
    list_editable = ("price", "old_price", "badge", "is_active")
    search_fields = ("name", "material", "description")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline, ProductImageInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "color_name", "color_hex", "stock", "is_default")
    list_filter = ("is_default",)
    list_editable = ("stock", "is_default")
    search_fields = ("product__name", "color_name", "sku")


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "variant", "is_primary", "alt")
    list_filter = ("is_primary",)
    search_fields = ("product__name", "alt")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "variant", "quantity", "unit_price", "subtotal")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "phone", "status", "total_amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "phone", "email", "address")
    readonly_fields = ("total_amount", "created_at")
    inlines = [OrderItemInline]
