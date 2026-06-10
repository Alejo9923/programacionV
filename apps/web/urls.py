from django.urls import path
from . import views

app_name = 'web'  # Namespace para usar {% url 'web:login' %} en los templates

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Catálogo
    path('products/', views.catalog_view, name='catalog'),
    path('products/<int:producto_id>/', views.product_detail_view, name='product_detail'),

    # Carrito
    path('cart/', views.cart_view, name='cart'),
    path('cart/items/<int:item_id>/update/', views.update_cart_item_view, name='update_cart_item'),
    path('cart/items/<int:item_id>/remove/', views.remove_cart_item_view, name='remove_cart_item'),
    path('cart/clear/', views.clear_cart_view, name='clear_cart'),

    # Checkout
    path('checkout/', views.checkout_view, name='checkout'),

    # Órdenes
    path('orders/', views.orders_view, name='orders'),
    path('orders/<int:orden_id>/', views.order_detail_view, name='order_detail'),
    path('orders/<int:orden_id>/confirm/', views.confirm_order_view, name='confirm_order'),
]