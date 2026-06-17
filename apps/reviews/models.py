"""
Modelo Review — app 'reviews' / Paso 2.5.

Una reseña representa la opinión de un usuario sobre un producto que
efectivamente compró. Se garantiza:
  - Una sola reseña por (usuario, producto) mediante unique_together.
  - Rating entre 1 y 5 mediante MinValueValidator y MaxValueValidator.
  - Acceso de escritura solo para compradores verificados (lógica en la vista).
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
    """
    Reseña de un producto realizada por un usuario que lo compró.

    Campos:
      producto   → Producto reseñado.
      usuario    → Autor de la reseña (AUTH_USER_MODEL).
      rating     → Puntaje entero de 1 a 5.
      comentario → Texto libre de la reseña.
      fecha      → Timestamp de creación, asignado automáticamente.

    Restricciones:
      unique_together (producto, usuario): un usuario no puede dejar más de
      una reseña por producto. Si lo intenta, la BD lanza IntegrityError
      que la vista captura y devuelve como 400.
    """

    # Referencia string para evitar importación circular con la app products.
    producto = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Producto',
    )

    # FK al modelo de usuario custom definido en AUTH_USER_MODEL.
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Usuario',
    )

    # Puntaje entero de 1 a 5. Los validators se aplican tanto en el ORM
    # como en DRF (full_clean() los ejecuta antes de guardar).
    rating = models.IntegerField(
        validators=[
            MinValueValidator(1, message='El rating mínimo es 1.'),
            MaxValueValidator(5, message='El rating máximo es 5.'),
        ],
        verbose_name='Rating',
    )

    # Texto libre de la reseña. blank=False: el comentario es obligatorio.
    comentario = models.TextField(verbose_name='Comentario')

    # Se asigna automáticamente al crear la reseña; nunca se modifica.
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')

    class Meta:
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'
        ordering = ['-fecha']
        # Garantiza que cada usuario deje máximo una reseña por producto.
        # La BD rechaza duplicados con IntegrityError; la vista lo captura.
        unique_together = [('producto', 'usuario')]

    def __str__(self):
        return f'Reseña de {self.usuario} para {self.producto} ({self.rating}★)'
