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
    path('orders/<int:orden_id>/invoice/', views.order_invoice_view, name='order_invoice'),
    # Dashboard de staff — productos, categorías y variantes
    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('dashboard/categories/', views.dashboard_categories_view, name='dashboard_categories'),
    path('dashboard/categories/<int:categoria_id>/delete/', views.dashboard_category_delete_view, name='dashboard_category_delete'),

    path('dashboard/products/', views.dashboard_products_view, name='dashboard_products'),
    path('dashboard/products/<int:producto_id>/edit/', views.dashboard_product_edit_view, name='dashboard_product_edit'),
    path('dashboard/products/<int:producto_id>/delete/', views.dashboard_product_delete_view, name='dashboard_product_delete'),

    path('dashboard/products/<int:producto_id>/variants/', views.dashboard_variants_view, name='dashboard_variants'),
    path('dashboard/variants/<int:variante_id>/edit/', views.dashboard_variant_edit_view, name='dashboard_variant_edit'),
    path('dashboard/variants/<int:variante_id>/delete/', views.dashboard_variant_delete_view, name='dashboard_variant_delete'),

    path('dashboard/orders/', views.dashboard_orders_view, name='dashboard_orders'),
    path('dashboard/orders/<int:orden_id>/', views.dashboard_order_detail_view, name='dashboard_order_detail'),
    path('dashboard/orders/<int:orden_id>/cancel/', views.dashboard_order_cancel_view, name='dashboard_order_cancel'),

    # Reseñas
    path('products/<int:producto_id>/reviews/', views.create_review_view, name='create_review'),
    path('reviews/<int:review_id>/delete/', views.delete_review_view, name='delete_review'),

]