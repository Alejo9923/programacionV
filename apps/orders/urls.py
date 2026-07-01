"""
URLs de la app 'orders'.

Todas las rutas quedan bajo el prefijo /api/ definido en config/urls.py.

Rutas del carrito (Integrante 1):
  GET    /api/cart/              → ver carrito con items y total
  POST   /api/cart/items/        → agregar item al carrito
  PUT    /api/cart/items/{id}/   → cambiar cantidad de un item
  DELETE /api/cart/items/{id}/   → quitar un item del carrito
  DELETE /api/cart/clear/        → vaciar carrito completo

Rutas de órdenes (Integrante 2):
  POST   /api/orders/checkout/       → convertir carrito en Order (Paso 2.2)
  POST   /api/orders/{id}/confirm/   → confirmación simulada      (Paso 2.3)
  GET    /api/orders/                → historial del usuario        (Paso 2.4)
  GET    /api/orders/{id}/           → detalle de una orden         (Paso 2.4)
  GET    /api/orders/{id}/invoice/   → descargar factura PDF        (Opcional C)
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
    # IMPORTANTE: esta ruta debe ir ANTES de orders/<int:pk>/ para que Django
    # no intente interpretar 'checkout' como un entero en el path converter.
    path('orders/checkout/', views.CheckoutView.as_view(), name='order-checkout'),

    # ── Historial y detalle de órdenes (Integrante 2 — Paso 2.4) ──────────
    # GET → lista SOLO las órdenes del usuario autenticado, ordenadas por -fecha.
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    # GET → detalle de una orden; verifica que pertenece a request.user (403 si no).
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),

    # ── Confirmación simulada (Integrante 2 — Paso 2.3) ───────────────────
    # POST → cambia estado a 'paid', descuenta stock y vacía el carrito.
    path('orders/<int:pk>/confirm/', views.ConfirmOrderView.as_view(), name='order-confirm'),

    # ── Factura PDF (Opcional C) ─────────────────────────────────────
    # GET → genera y descarga el PDF de la factura de una orden 'paid'.
    # La ruta con dos segmentos debe ir ANTES de orders/<int:pk>/ para
    # que Django la evalúe primero y no confunda 'invoice' como segundo pk.
    path('orders/<int:pk>/invoice/', views.OrderInvoiceView.as_view(), name='order-invoice'),
]