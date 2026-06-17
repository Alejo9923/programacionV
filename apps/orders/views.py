"""
Vistas de la app 'orders' — Integrante 2.

Mantiene las vistas de carrito del Integrante 1 e incorpora:
  - CheckoutView      (Paso 2.2) — convierte el carrito en una Order.
  - ConfirmOrderView  (Paso 2.3) — confirmación simulada, descuenta stock.
  - OrderListView     (Paso 2.4) — historial de órdenes del usuario.
  - OrderDetailView   (Paso 2.4) — detalle de una orden con sus items.
"""

from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Cart, CartItem, Order, OrderItem
from .serializers import (
    CartSerializer,
    CartItemSerializer,
    OrderSerializer,
)
from apps.products.models import ProductVariant


# ──────────────────────────────────────────────
#  Vistas existentes del Integrante 1 (carrito)
# ──────────────────────────────────────────────

class CartView(APIView):
    """
    GET /api/cart/ → devuelve el carrito del usuario autenticado con items y total.

    Si el usuario no tiene carrito todavía, lo crea automáticamente.
    Esto garantiza que siempre haya un carrito disponible sin pasos extra.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # get_or_create devuelve (objeto, creado).
        # Si no existe el carrito, lo crea en ese momento.
        cart, _ = Cart.objects.get_or_create(usuario=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartItemCreateView(APIView):
    """
    POST /api/cart/items/ → agrega un item al carrito.

    Body esperado: { "variante_id": 1, "cantidad": 2 }

    Lógica:
    - Si la variante ya está en el carrito, suma la cantidad.
    - Si no existe, crea un nuevo CartItem.
    - Verifica que haya stock suficiente antes de agregar.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Obtenemos o creamos el carrito del usuario
        cart, _ = Cart.objects.get_or_create(usuario=request.user)

        # Validamos el body con el serializer
        serializer = CartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        variante_id = serializer.validated_data['variante_id']
        cantidad = serializer.validated_data['cantidad']

        # Verificamos que la variante existe
        variante = get_object_or_404(ProductVariant, pk=variante_id)

        # Verificamos stock disponible
        if variante.stock < cantidad:
            return Response(
                {"error": f"Stock insuficiente. Disponible: {variante.stock}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Si el item ya existe en el carrito, sumamos la cantidad
        cart_item, creado = CartItem.objects.get_or_create(
            carrito=cart,
            variante=variante,
            defaults={'cantidad': cantidad}
        )

        if not creado:
            # El item ya existía — verificamos stock para la cantidad total
            nueva_cantidad = cart_item.cantidad + cantidad
            if variante.stock < nueva_cantidad:
                return Response(
                    {"error": f"Stock insuficiente. Disponible: {variante.stock}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.cantidad = nueva_cantidad
            cart_item.save()

        return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    PUT    /api/cart/items/{id}/ → cambia la cantidad de un item
    DELETE /api/cart/items/{id}/ → elimina un item del carrito

    Solo el dueño del carrito puede modificar sus items.
    """
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filtramos por el carrito del usuario autenticado.
        # Así un usuario no puede modificar items del carrito de otro.
        return CartItem.objects.filter(carrito__usuario=self.request.user)


class CartClearView(APIView):
    """
    DELETE /api/cart/clear/ → vacía el carrito completo del usuario.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(usuario=request.user)
        # Borramos todos los items del carrito de una sola vez.
        cart.items.all().delete()
        return Response({"mensaje": "Carrito vaciado."}, status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────
#  CheckoutView — Paso 2.2
# ──────────────────────────────────────────────

class CheckoutView(APIView):
    """
    POST /api/orders/checkout/ — Convierte el carrito activo en una Order.

    Todo el proceso ocurre dentro de transaction.atomic(): si cualquier paso
    falla (stock insuficiente, error de BD, etc.) se hace rollback completo
    y no queda ninguna orden ni ítem parcialmente creado.

    Proceso:
      1. Obtener carrito — devuelve 400 si no existe o está vacío.
      2. Verificar stock de cada ítem — devuelve 400 con detalle de la variante.
      3. Calcular total sumando (precio_base + precio_extra) × cantidad.
      4. Crear Order con estado 'pending'.
      5. Crear un OrderItem por cada CartItem, copiando el precio como snapshot.
      6. NO se descuenta stock aquí (se hace en el paso 2.3).
      7. NO se vacía el carrito aquí.

    Respuesta 201: datos de la Order creada con sus items.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        with transaction.atomic():

            # ── Paso 1: Obtener el carrito del usuario ─────────────────────
            # Usamos get() en lugar de get_or_create() para detectar cuando
            # el usuario nunca tuvo carrito (Cart.DoesNotExist).
            try:
                cart = Cart.objects.get(usuario=request.user)
            except Cart.DoesNotExist:
                return Response(
                    {"error": "No tenés un carrito activo."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Traemos todos los ítems del carrito con sus variantes en una
            # sola consulta usando select_related para evitar N+1 queries.
            items = cart.items.select_related(
                'variante__producto'
            ).all()

            # Carrito vacío → no tiene sentido crear una orden sin productos.
            if not items.exists():
                return Response(
                    {"error": "El carrito está vacío. Agregá productos antes de finalizar la compra."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ── Paso 2: Verificar stock de CADA ítem ──────────────────────
            # Lo hacemos antes de crear nada para detectar todos los problemas
            # de stock y devolver un error descriptivo sin efectos secundarios.
            for item in items:
                variante = item.variante
                if variante.stock < item.cantidad:
                    return Response(
                        {
                            "error": (
                                f"Stock insuficiente para '{variante}'. "
                                f"Disponible: {variante.stock}, "
                                f"solicitado: {item.cantidad}."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # ── Paso 3: Calcular el total de la orden ─────────────────────
            # precio_unitario = precio_base del producto + precio_extra de la variante.
            # Multiplicamos por la cantidad de unidades de cada ítem.
            total = sum(
                (item.variante.producto.precio_base + item.variante.precio_extra)
                * item.cantidad
                for item in items
            )

            # ── Paso 4: Crear la Order ─────────────────────────────────────
            # Estado inicial siempre es 'pending'; cambia en el paso 2.3
            # cuando se simula la confirmación del pago.
            order = Order.objects.create(
                usuario=request.user,
                total=total,
                estado=Order.Estado.PENDING,
            )

            # ── Paso 5: Crear los OrderItems con precio snapshot ───────────
            # precio_unitario se copia del precio actual de la variante y
            # queda congelado en la orden — nunca se actualiza si el precio
            # del producto cambia en el futuro.
            order_items = [
                OrderItem(
                    orden=order,
                    variante=item.variante,
                    cantidad=item.cantidad,
                    precio_unitario=(
                        item.variante.producto.precio_base + item.variante.precio_extra
                    ),
                )
                for item in items
            ]
            # bulk_create inserta todos los ítems en una sola query SQL,
            # más eficiente que llamar a .create() dentro de un loop.
            OrderItem.objects.bulk_create(order_items)

            # ── Pasos 6 y 7: SIN descontar stock, SIN vaciar carrito ───────
            # El descuento de stock ocurre en la confirmación (paso 2.3).
            # El carrito se mantiene para permitir que el usuario lo revise
            # o vuelva a comprar si la orden no se confirma.

        # ── Respuesta 201 ─────────────────────────────────────────────────
        # Fuera del bloque atomic (ya commiteado). Serializamos la orden
        # recién creada con todos sus items para la respuesta al cliente.
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ──────────────────────────────────────────────
#  ConfirmOrderView — Paso 2.3
# ──────────────────────────────────────────────

class ConfirmOrderView(APIView):
    """
    POST /api/orders/{id}/confirm/ — Confirmación simulada de compra.

    Diseñado para ser reemplazado en el futuro por un webhook real de
    MercadoPago sin necesidad de refactorizar el resto del código:
    bastará con que el webhook llame a la misma lógica de negocio aquí
    centralizada (cambiar estado, descontar stock, vaciar carrito).

    Proceso dentro de transaction.atomic():
      1. Cambiar Order.estado a 'paid'.
      2. Descontar stock de cada variante usando select_for_update().
      3. Vaciar el carrito del usuario.

    Por qué todo va dentro de atomic():
      Si el descuento de stock de la variante 3 falla después de haber
      actualizado la variante 1 y 2, el rollback revierte todo: la orden
      vuelve a 'pending', el stock queda intacto y el carrito no se vacía.
      Sin atomic(), quedaríamos con un estado inconsistente en la BD.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        # ── Obtener la orden ───────────────────────────────────────────────
        # get_object_or_404 devuelve 404 automáticamente si el ID no existe,
        # evitando exponer si el recurso existe o no a usuarios no autorizados
        # (ese control lo hacemos explícitamente en el paso siguiente).
        order = get_object_or_404(Order, pk=pk)

        # ── Verificar propiedad ────────────────────────────────────────────
        # Solo el dueño de la orden puede confirmarla.
        # Devolvemos 403 Forbidden en lugar de 404 para ser explícitos:
        # el recurso existe, pero el usuario no tiene permiso sobre él.
        if order.usuario != request.user:
            return Response(
                {"error": "No tenés permiso para confirmar esta orden."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # ── Verificar estado ───────────────────────────────────────────────
        # Solo se pueden confirmar órdenes en estado 'pending'.
        # Si ya está 'paid' o 'cancelled', no tiene sentido procesarla de nuevo.
        if order.estado != Order.Estado.PENDING:
            return Response(
                {
                    "error": (
                        f"La orden ya fue procesada. "
                        f"Estado actual: '{order.get_estado_display()}'."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():

            # ── Paso 1: Marcar la orden como pagada ────────────────────────
            # Se hace primero para que, si algo falla más abajo, el rollback
            # revierte también este cambio y la orden vuelve a 'pending'.
            order.estado = Order.Estado.PAID
            order.save(update_fields=['estado'])

            # ── Paso 2: Descontar stock con select_for_update() ────────────
            # select_for_update() adquiere un bloqueo a nivel de fila (row-level
            # lock) sobre cada variante dentro de la transacción.
            # Sin este bloqueo, dos requests simultáneas podrían leer el mismo
            # stock=5, descuentan 3 cada una, y ambas guardan stock=2 en lugar
            # del correcto stock=-1 (condición de carrera / lost update).
            # El bloqueo hace que la segunda request espere hasta que la primera
            # haga commit o rollback antes de leer el valor actualizado.
            items = order.items.select_related('variante').all()

            for item in items:
                # Bloqueamos la fila de la variante para esta transacción.
                variante = (
                    item.variante.__class__._default_manager
                    .select_for_update()
                    .get(pk=item.variante_id)
                )
                variante.stock -= item.cantidad
                # update_fields limita el UPDATE a solo la columna 'stock',
                # evitando sobreescribir otros campos que puedan haber cambiado.
                variante.save(update_fields=['stock'])

            # ── Paso 3: Vaciar el carrito ──────────────────────────────────
            # El carrito se vacía dentro del atomic() para que, si falla el
            # descuento de stock, también se revierta este paso y el usuario
            # conserve su carrito intacto.
            # Usamos get_or_create por si el usuario no tiene carrito todavía
            # (caso borde que evita un DoesNotExist inesperado).
            try:
                cart = Cart.objects.get(usuario=request.user)
                cart.items.all().delete()
            except Cart.DoesNotExist:
                # Si no tiene carrito no hay nada que vaciar, continuamos.
                pass

        # ── Respuesta 200 ─────────────────────────────────────────────────
        # Fuera del bloque atomic (ya commiteado).
        return Response(
            {
                "mensaje": "Compra confirmada",
                "orden_id": order.pk,
                "estado": order.estado,
                "total": str(order.total),
            },
            status=status.HTTP_200_OK,
        )


# ──────────────────────────────────────────────
#  OrderListView — Paso 2.4
# ──────────────────────────────────────────────

class OrderListView(APIView):
    """
    GET /api/orders/ — Historial de órdenes del usuario autenticado.

    Devuelve ÚNICAMENTE las órdenes que pertenecen a request.user.
    El filtro por usuario es obligatorio: sin él cualquier usuario autenticado
    podría ver órdenes ajenas, lo cual es una falla de seguridad grave.

    Las órdenes se devuelven ordenadas por fecha descendente (-fecha) para
    que la más reciente aparezca siempre primera, tal como espera el usuario.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filtramos estrictamente por request.user para que cada usuario
        # solo pueda ver su propio historial, nunca el de otros.
        # select_related('items') trae los OrderItems en la misma query
        # evitando N+1 al serializar cada orden con sus items anidados.
        orders = (
            Order.objects
            .filter(usuario=request.user)
            .prefetch_related('items')
            .order_by('-fecha')
        )
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────
#  OrderDetailView — Paso 2.4
# ──────────────────────────────────────────────

class OrderDetailView(APIView):
    """
    GET /api/orders/{id}/ — Detalle de una orden con todos sus items.

    Pasos:
      1. Obtener la orden por pk (404 si no existe).
      2. Verificar que pertenece a request.user (403 si no es dueño).
      3. Serializar y devolver con items anidados.

    Por qué verificamos la propiedad explícitamente:
      Usar filter(usuario=request.user, pk=pk) devolvería 404 tanto si la
      orden no existe como si existe pero es ajena, lo que oculta la razón
      real del rechazo. Separar los dos controles (404 vs 403) da respuestas
      más claras y facilita el debugging durante el desarrollo.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Paso 1: Obtener la orden — 404 automático si el id no existe.
        order = get_object_or_404(Order, pk=pk)

        # Paso 2: Verificar que la orden pertenece al usuario autenticado.
        # Usamos 403 Forbidden (no 404) para ser explícitos: el recurso
        # existe pero el usuario no tiene permiso sobre él.
        if order.usuario != request.user:
            return Response(
                {"error": "No tenés permiso para ver esta orden."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Paso 3: Serializar la orden con sus items anidados.
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)