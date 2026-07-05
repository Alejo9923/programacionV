"""
Serializers de la app 'orders' — Integrante 2 / Paso 2.2.

Define la representación JSON de las respuestas del endpoint de checkout:
  - OrderItemSerializer: muestra cada línea de la orden (variante, cantidad, precio snapshot).
  - OrderSerializer:     muestra la orden completa con sus items anidados y el total.

Los serializers de carrito (CartSerializer / CartItemSerializer) se mantienen
tal como los dejó el Integrante 1.
"""

from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem
from apps.products.serializers import ProductVariantSerializer


# ──────────────────────────────────────────────
#  Serializers existentes del Integrante 1 (carrito)
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
#  Serializers nuevos — Paso 2.2 (checkout)
# ──────────────────────────────────────────────

class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer de solo lectura para cada línea de una Order.

    Devuelve los datos mínimos necesarios en la respuesta del checkout:
      - variante_id:     ID de la variante comprada.
      - cantidad:        Unidades.
      - precio_unitario: Precio snapshot al momento de la compra
                         (NO el precio actual de la variante).

    Es read_only en su totalidad porque los OrderItems se crean
    internamente en CheckoutView, nunca desde el body de la request.
    """
    variante = ProductVariantSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'variante',
            'variante_id',      # FK ID — suficiente para identificar la variante
            'cantidad',
            'precio_unitario',  # Snapshot: precio fijo en el momento de la compra
        ]
        # Todos los campos son de solo lectura: el serializer solo se usa
        # para serializar la respuesta, nunca para deserializar input.
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer de solo lectura para una Order completa.

    Usado exclusivamente en la respuesta 201 del endpoint de checkout.
    Incluye los items anidados vía OrderItemSerializer para que el cliente
    pueda confirmar exactamente qué se compró y a qué precio.

    Campos devueltos:
      - id:     ID de la orden recién creada.
      - total:  Importe total calculado al momento del checkout.
      - estado: Siempre 'pending' al crear (se actualiza en el paso 2.3).
      - fecha:  Timestamp de creación (auto_now_add).
      - items:  Lista de OrderItems con variante_id, cantidad y precio_unitario.
    """

    # Items anidados — usa related_name='items' definido en OrderItem.
    # many=True porque una orden tiene múltiples líneas.
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'total',
            'estado',
            'fecha',
            'items',
        ]
        read_only_fields = fields


# ──────────────────────────────────────────────
#  Serializer para el dashboard de staff (gestión de órdenes)
# ──────────────────────────────────────────────

class AdminOrderSerializer(OrderSerializer):
    """
    Extiende OrderSerializer agregando el email del dueño de la orden.

    Se usa solo en las vistas de administración, donde el staff ve órdenes
    de todos los usuarios (no solo las propias) y necesita saber de quién
    es cada una — el OrderSerializer normal no lo incluye porque en el resto
    de la API cada usuario solo ve sus propias órdenes.
    """
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ['usuario_email']
        read_only_fields = fields