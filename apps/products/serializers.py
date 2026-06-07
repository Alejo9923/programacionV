from rest_framework import serializers
from .models import Category, Product


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


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo Product.

    Incluye categoria_nombre como campo extra de solo lectura para que
    la respuesta JSON muestre el nombre legible de la categoría además
    del ID. Así el frontend no necesita hacer una segunda consulta.

    Ejemplo de respuesta:
    {
        "id": 1,
        "nombre": "Remera básica",
        "precio_base": "15.00",
        "categoria": 2,           ← ID (para crear/editar)
        "categoria_nombre": "Remeras",  ← nombre legible (solo lectura)
        ...
    }
    """

    # Campo extra que lee el nombre desde la relación ForeignKey.
    # source='categoria.nombre' navega la relación automáticamente.
    # read_only=True porque es solo informativo, no se usa al crear/editar.
    categoria_nombre = serializers.CharField(
        source='categoria.nombre',
        read_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'nombre',
            'descripcion',
            'precio_base',
            'categoria',        # ID de la categoría (requerido al crear)
            'categoria_nombre', # Nombre legible (solo en respuestas)
            'imagen',
            'activo',
        ]

    # NOTA: Las variantes anidadas se agregarán en el módulo 1.4
    # sin necesidad de modificar nada más de este serializer.