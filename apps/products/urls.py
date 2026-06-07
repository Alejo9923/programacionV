from django.urls import path
from . import views

# URLs del módulo de productos y categorías.
# Todas quedan bajo el prefijo /api/ que se define en config/urls.py

urlpatterns = [
    # Categorías
    # GET  /api/categories/      → lista pública
    # POST /api/categories/      → crear (solo admin)
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list'),

    # GET    /api/categories/{id}/ → detalle público
    # PUT    /api/categories/{id}/ → editar (solo admin)
    # DELETE /api/categories/{id}/ → borrar (solo admin)
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),

    # Productos
    # GET  /api/products/        → lista pública con filtros
    # POST /api/products/        → crear (solo admin)
    path('products/', views.ProductListCreateView.as_view(), name='product-list'),

    # GET    /api/products/{id}/ → detalle público
    # PUT    /api/products/{id}/ → editar (solo admin)
    # DELETE /api/products/{id}/ → borrar (solo admin)
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
]