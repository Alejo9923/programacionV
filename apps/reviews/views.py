"""
Vistas de la app 'reviews' — Paso 2.5.

Implementa los tres endpoints de reseñas:
  - ReviewListCreateView : GET  /api/products/{id}/reviews/  (público)
                           POST /api/products/{id}/reviews/  (autenticado + comprador)
  - ReviewDeleteView     : DELETE /api/reviews/{id}/         (autenticado + autor)
"""

from django.db import IntegrityError
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import OrderItem
from apps.products.models import Product
from .models import Review
from .serializers import ReviewSerializer


class ReviewListCreateView(APIView):
    """
    GET  /api/products/{id}/reviews/ — Lista reseñas de un producto (público).
    POST /api/products/{id}/reviews/ — Crea una reseña (solo compradores verificados).
    """

    def get_permissions(self):
        # GET es público: cualquiera puede leer las reseñas sin autenticarse.
        # POST requiere autenticación: además verificamos la compra en la vista.
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request, producto_id):
        """
        Lista todas las reseñas del producto junto con el rating promedio.

        Respuesta:
          {
            "rating_promedio": 4.2,
            "total_resenas": 3,
            "resenas": [...]
          }

        El rating promedio se calcula con aggregate(Avg('rating')) para
        delegar el cálculo a la BD en una sola query en lugar de hacerlo
        en Python con un loop.
        """
        # 404 si el producto no existe.
        producto = get_object_or_404(Product, pk=producto_id)

        reviews = Review.objects.filter(producto=producto).order_by('-fecha')

        # aggregate() devuelve un dict; si no hay reseñas, el valor es None.
        resultado = reviews.aggregate(promedio=Avg('rating'))
        rating_promedio = resultado['promedio']

        # Redondeamos a 1 decimal para presentación; mantenemos None si no hay reseñas.
        if rating_promedio is not None:
            rating_promedio = round(rating_promedio, 1)

        serializer = ReviewSerializer(reviews, many=True)
        return Response(
            {
                'rating_promedio': rating_promedio,
                'total_resenas': reviews.count(),
                'resenas': serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, producto_id):
        """
        Crea una nueva reseña para el producto.

        Verificaciones previas a la creación:
          1. El producto debe existir (404 si no).
          2. El usuario debe haber comprado el producto en una orden 'paid' (403 si no).
          3. El usuario no debe tener ya una reseña del mismo producto (400 vía IntegrityError).

        El producto y el usuario se asignan automáticamente: el cliente solo
        envía rating y comentario en el body.
        """
        # Paso 1: Verificar que el producto existe.
        producto = get_object_or_404(Product, pk=producto_id)

        # Paso 2: Verificar que el usuario compró este producto.
        # La cadena de FK es: OrderItem → variante (ProductVariant) → producto (Product)
        # y también filtramos que la Order del OrderItem esté en estado 'paid'.
        compro = OrderItem.objects.filter(
            orden__usuario=request.user,
            orden__estado='paid',
            variante__producto=producto,
        ).exists()

        if not compro:
            return Response(
                {'error': 'Solo usuarios que compraron este producto pueden reseñar.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Paso 3: Validar el body (rating y comentario).
        serializer = ReviewSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Paso 4: Intentar crear la reseña.
        # Si el usuario ya tiene una reseña del mismo producto, la BD lanza
        # IntegrityError por la restricción unique_together(producto, usuario).
        # Lo capturamos y devolvemos 400 con un mensaje claro.
        try:
            review = serializer.save(
                producto=producto,
                usuario=request.user,
            )
        except IntegrityError:
            return Response(
                {'error': 'Ya dejaste una reseña para este producto.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class ReviewDeleteView(APIView):
    """
    DELETE /api/reviews/{id}/ — Elimina una reseña.

    Solo el autor de la reseña puede borrarla.
    Cualquier otro usuario autenticado recibe 403 Forbidden.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        # get_object_or_404 devuelve 404 automáticamente si la reseña no existe.
        review = get_object_or_404(Review, pk=pk)

        # Verificar que el usuario autenticado es el autor de la reseña.
        # Usamos 403 Forbidden (no 404) para ser explícitos: el recurso existe
        # pero el usuario no tiene permiso de eliminarlo.
        if review.usuario != request.user:
            return Response(
                {'error': 'No tenés permiso para eliminar esta reseña.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        review.delete()
        # 204 No Content: operación exitosa, sin cuerpo de respuesta.
        return Response(status=status.HTTP_204_NO_CONTENT)
