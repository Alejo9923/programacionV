from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.serializers import ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer para cada item del carrito.

    Muestra los datos de la variante anidados (talla, color, stock, precio)
    y calcula el subtotal de ese item (precio_variante × cantidad).
    """
    # Muestra los datos completos de la variante en lugar de solo el ID.
    # read_only=True porque la variante se especifica al crear via variante_id.
    variante = ProductVariantSerializer(read_only=True)

    # Campo de solo escritura: el cliente envía el ID de la variante al agregar
    # un item. write_only=True para que no aparezca en las respuestas GET.
    variante_id = serializers.IntegerField(write_only=True)

    # Campo calculado: precio_total de la variante × cantidad del item.
    # SerializerMethodField porque requiere acceder a dos campos del objeto.
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'variante',     # Datos completos (solo lectura)
            'variante_id',  # ID para crear/editar (solo escritura)
            'cantidad',
            'subtotal',     # precio_total × cantidad (solo lectura)
        ]

    def get_subtotal(self, obj):
        # obj.variante.precio_total no existe como campo en el modelo,
        # lo calculamos igual que en ProductVariantSerializer.
        precio = obj.variante.producto.precio_base + obj.variante.precio_extra
        return precio * obj.cantidad


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer para el carrito completo.

    Muestra todos los items con sus subtotales y calcula el total general.
    El usuario se asigna automáticamente desde request.user en la vista.
    """
    # Items anidados: usa el related_name='items' definido en CartItem.
    # many=True porque un carrito tiene múltiples items.
    items = CartItemSerializer(many=True, read_only=True)

    # Total general del carrito: suma de todos los subtotales.
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id',
            'items',
            'total',
        ]

    def get_total(self, obj):
        # Iteramos todos los items y sumamos sus subtotales.
        total = 0
        for item in obj.items.all():
            precio = item.variante.producto.precio_base + item.variante.precio_extra
            total += precio * item.cantidad
        return total