"""
URLs de la app 'reviews' — Paso 2.5.

Rutas registradas bajo el prefijo /api/ de config/urls.py:

  GET    /api/products/{id}/reviews/  → listar reseñas del producto (público)
  POST   /api/products/{id}/reviews/  → crear reseña (autenticado + comprador)
  DELETE /api/reviews/{id}/           → eliminar reseña propia (autenticado)
"""

from django.urls import path
from . import views

urlpatterns = [
    # GET  → lista reseñas + rating promedio del producto (acceso público)
    # POST → crea una reseña; requiere autenticación y compra verificada
    path(
        'products/<int:producto_id>/reviews/',
        views.ReviewListCreateView.as_view(),
        name='review-list-create',
    ),

    # DELETE → elimina la reseña; solo el autor puede hacerlo
    path(
        'reviews/<int:pk>/',
        views.ReviewDeleteView.as_view(),
        name='review-delete',
    ),
]
