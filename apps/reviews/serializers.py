"""
Serializer de la app 'reviews' — Paso 2.5.

ReviewSerializer se usa tanto para listar reseñas (GET) como para crearlas
(POST). Los campos producto y usuario son de solo lectura porque se asignan
automáticamente en la vista (desde la URL y desde request.user), nunca desde
el body de la request.
"""

from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer de Review.

    Campos expuestos:
      - id:          Identificador de la reseña.
      - usuario_id:  ID del autor (solo lectura, asignado desde request.user).
      - producto_id: ID del producto (solo lectura, asignado desde la URL).
      - rating:      Puntaje 1-5 (los validators del modelo se ejecutan en is_valid).
      - comentario:  Texto de la reseña.
      - fecha:       Timestamp de creación (solo lectura, auto_now_add).

    Los campos read_only no se incluyen en la validación de POST,
    lo que significa que el cliente solo necesita enviar rating y comentario.
    """

    class Meta:
        model = Review
        fields = [
            'id',
            'usuario_id',   # FK ID del autor — solo lectura
            'producto_id',  # FK ID del producto — solo lectura
            'rating',
            'comentario',
            'fecha',        # auto_now_add — solo lectura
        ]
        read_only_fields = ['id', 'usuario_id', 'producto_id', 'fecha']
