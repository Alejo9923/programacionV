from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters
from .models import Category, Product, ProductVariant
from .serializers import CategorySerializer, ProductSerializer, ProductVariantSerializer
from .permissions import IsAdminOrReadOnly


class ProductVariantListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/products/{producto_id}/variants/ → lista variantes de un producto (público)
    POST /api/products/{producto_id}/variants/ → crea una variante nueva (solo admin)

    Las variantes siempre están asociadas a un producto específico.
    El producto_id viene en la URL, no en el body.
    """
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        # self.kwargs['producto_id'] lee el parámetro dinámico de la URL.
        # Así solo devolvemos las variantes del producto solicitado.
        return ProductVariant.objects.filter(
            producto_id=self.kwargs['producto_id']
        ).select_related('producto')  # select_related evita N+1 al calcular precio_total

    def perform_create(self, serializer):
        # Al crear, asignamos automáticamente el producto desde la URL.
        # Así el cliente no necesita enviar producto_id en el body.
        producto = Product.objects.get(pk=self.kwargs['producto_id'])
        serializer.save(producto=producto)


class ProductVariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/variants/{id}/ → detalle de una variante (público)
    PUT    /api/variants/{id}/ → editar variante (solo admin)
    DELETE /api/variants/{id}/ → borrar variante (solo admin)

    Se accede por el ID directo de la variante, no por el producto.
    Útil para editar stock, precio_extra o color de una variante específica.
    """
    queryset = ProductVariant.objects.all().select_related('producto')
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAdminOrReadOnly]

class CategoryListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/categories/ → lista todas las categorías (público)
    POST /api/categories/ → crea una categoría nueva (solo admin)
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

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