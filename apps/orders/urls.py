"""
URLs de la app 'orders'.

Todas las rutas quedan bajo el prefijo /api/ definido en config/urls.py.

Rutas del carrito (Integrante 1):
  GET    /api/cart/              → ver carrito con items y total
  POST   /api/cart/items/        → agregar item al carrito
  PUT    /api/cart/items/{id}/   → cambiar cantidad de un item
  DELETE /api/cart/items/{id}/   → quitar un item del carrito
  DELETE /api/cart/clear/        → vaciar carrito completo

Rutas de órdenes (Integrante 2 — Paso 2.2):
  POST   /api/orders/checkout/   → convertir carrito en Order (checkout)
"""

from django.urls import path
from . import views

urlpatterns = [
    # ── Carrito (Integrante 1) ─────────────────────────────────────────────
    path('cart/', views.CartView.as_view(), name='cart-detail'),
    path('cart/items/', views.CartItemCreateView.as_view(), name='cart-item-create'),
    path('cart/items/<int:pk>/', views.CartItemDetailView.as_view(), name='cart-item-detail'),
    path('cart/clear/', views.CartClearView.as_view(), name='cart-clear'),

    # ── Checkout (Integrante 2 — Paso 2.2) ────────────────────────────────
    # POST → verifica carrito, stock, calcula total y crea Order + OrderItems.
    path('orders/checkout/', views.CheckoutView.as_view(), name='order-checkout'),

    # ── Confirmación simulada (Integrante 2 — Paso 2.3) ───────────────────
    # POST → cambia estado a 'paid', descuenta stock y vacía el carrito.
    # El {id} identifica la Order a confirmar.
    path('orders/<int:pk>/confirm/', views.ConfirmOrderView.as_view(), name='order-confirm'),
]