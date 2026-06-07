from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from .permissions import IsAdminOrReadOnly


class CategoryListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/categories/ → lista todas las categorías (público)
    POST /api/categories/ → crea una categoría nueva (solo admin)

    Usamos ListCreateAPIView de DRF porque combina las dos operaciones
    en una sola clase, evitando repetir lógica.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]  # Permiso que creamos en el paso anterior


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/categories/{id}/ → detalle de una categoría (público)
    PUT    /api/categories/{id}/ → editar categoría (solo admin)
    DELETE /api/categories/{id}/ → borrar categoría (solo admin)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/products/ → lista productos activos (público, con filtros)
    POST /api/products/ → crea un producto nuevo (solo admin)

    Soporta los siguientes query params:
    - ?categoria=1         → filtra por ID de categoría (django-filter)
    - ?search=remera       → búsqueda en nombre y descripción
    - ?ordering=precio_base → ordena por precio o nombre
    - ?precio_min=10       → filtro manual de precio mínimo
    - ?precio_max=100      → filtro manual de precio máximo
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]

    # filter_backends define qué motores de filtrado están activos en esta vista.
    # DjangoFilterBackend → para filtros exactos (categoria=1)
    # SearchFilter         → para búsqueda de texto (?search=...)
    # OrderingFilter       → para ordenamiento (?ordering=...)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = ['categoria']          # Campos habilitados para filtro exacto
    search_fields = ['nombre', 'descripcion'] # Campos donde busca SearchFilter
    ordering_fields = ['precio_base', 'nombre'] # Campos por los que se puede ordenar

    def get_queryset(self):
        """
        Sobreescribimos get_queryset (en lugar de definir queryset directo)
        para poder aplicar los filtros de precio_min y precio_max
        dinámicamente según los parámetros que lleguen en la request.
        """
        # Solo mostramos productos activos; select_related evita N+1 queries
        # al acceder a categoria.nombre desde el serializer.
        queryset = Product.objects.filter(activo=True).select_related('categoria')

        precio_min = self.request.query_params.get('precio_min')
        precio_max = self.request.query_params.get('precio_max')

        if precio_min:
            queryset = queryset.filter(precio_base__gte=precio_min)
        if precio_max:
            queryset = queryset.filter(precio_base__lte=precio_max)

        return queryset


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/products/{id}/ → detalle de un producto (público)
    PUT    /api/products/{id}/ → editar producto (solo admin)
    DELETE /api/products/{id}/ → borrar producto (solo admin)

    Usamos el queryset completo (sin filtrar activo=True) para que
    el admin pueda ver y editar también productos inactivos por su ID.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]