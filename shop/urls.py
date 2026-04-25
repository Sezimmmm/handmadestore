from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("catalog/", views.catalog, name="catalog"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<slug:slug>/", views.cart_add, name="cart_add"),
    path("cart/remove/<slug:slug>/", views.cart_remove, name="cart_remove"),
    path("cart/clear/", views.cart_clear, name="cart_clear"),
    path("checkout/", views.checkout, name="checkout"),
    path("checkout/success/", views.checkout_success, name="checkout_success"),
    path("about/", views.about, name="about"),
    path("personalization/", views.personalization, name="personalization"),
    path(
        "personalization/add-to-cart/",
        views.personalization_add_to_cart,
        name="personalization_add_to_cart",
    ),
    path(
        "cart/remove-builder/<str:builder_id>/",
        views.cart_remove_builder,
        name="cart_remove_builder",
    ),
    path("contacts/", views.contacts, name="contacts"),
    path("account/", views.account, name="account"),
]
