from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from apps.products.models import ProductVariant


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