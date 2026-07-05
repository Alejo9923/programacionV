from rest_framework import serializers
from .models import Category, Product, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Category.
    Convierte instancias de Category a JSON y viceversa.
    El slug es de solo lectura porque se genera automáticamente en el modelo.
    """
    class Meta:
        model = Category
        fields = ['id', 'nombre', 'slug', 'descripcion']
        # El slug lo genera el modelo en save(), el cliente no debe enviarlo.
        read_only_fields = ['slug']


class ProductVariantSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo ProductVariant.
    
    Se usa de dos formas:
    - Anidado dentro de ProductSerializer → muestra las variantes al listar productos.
    - Independiente en las vistas de variantes → para crear/editar/borrar una variante.
    """
    # Campo extra de solo lectura que muestra el precio total de la variante
    # (precio_base del producto + precio_extra de la variante).
    # Se calcula con SerializerMethodField porque requiere acceder a dos modelos.
    precio_total = serializers.SerializerMethodField()
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = ProductVariant
        fields = [
            'id',
            'producto',     # ID del producto (requerido al crear)
            'producto_nombre',
            'talla',        # S / M / L / XL
            'color',
            'stock',
            'precio_extra', # Costo adicional sobre el precio_base
            'precio_total', # precio_base + precio_extra (solo lectura)
        ]
        # producto se asigna automáticamente desde la URL, no desde el body
        read_only_fields = ['producto', 'precio_total']

    def get_precio_total(self, obj):
        # obj es la instancia de ProductVariant.
        # obj.producto.precio_base accede al producto relacionado via FK.
        return obj.producto.precio_base + obj.precio_extra


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Product.
    
    Incluye:
    - categoria_nombre: nombre legible de la categoría (solo lectura).
    - variantes: lista de todas las variantes del producto (solo lectura).
      Se muestran anidadas en la respuesta; para crear/editar variantes
      se usan los endpoints propios de variantes.
    """
    # Muestra el nombre de la categoría además del ID.
    categoria_nombre = serializers.CharField(
        source='categoria.nombre',
        read_only=True
    )

    # Variantes anidadas: usa el related_name='variantes' definido en el modelo.
    # many=True porque un producto puede tener múltiples variantes.
    # read_only=True porque las variantes se gestionan por sus propios endpoints.
    variantes = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'nombre',
            'descripcion',
            'precio_base',
            'categoria',        # ID (requerido al crear/editar)
            'categoria_nombre', # Nombre legible (solo lectura)
            'imagen',
            'activo',
            'variantes',        # Lista de variantes anidadas (solo lectura)
        ]