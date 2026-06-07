from django.urls import path
from . import views

# URLs del módulo de carrito.
# Todas quedan bajo el prefijo /api/ que se define en config/urls.py

urlpatterns = [
    # GET /api/cart/ → ver carrito con items y total
    path('cart/', views.CartView.as_view(), name='cart-detail'),

    # POST /api/cart/items/ → agregar item al carrito
    path('cart/items/', views.CartItemCreateView.as_view(), name='cart-item-create'),

    # PUT    /api/cart/items/{id}/ → cambiar cantidad
    # DELETE /api/cart/items/{id}/ → quitar un item
    path('cart/items/<int:pk>/', views.CartItemDetailView.as_view(), name='cart-item-detail'),

    # DELETE /api/cart/clear/ → vaciar carrito completo
    path('cart/clear/', views.CartClearView.as_view(), name='cart-clear'),
]