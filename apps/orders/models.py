from django.conf import settings
from django.db import models


# ──────────────────────────────────────────────
#  Modelos existentes (Integrante 1 / base)
# ──────────────────────────────────────────────

class Cart(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
    )
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.usuario}"


class CartItem(models.Model):
    carrito = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
    )
    # Referencia lazy para no depender de que products esté importado aún
    variante = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.CASCADE,
    )
    cantidad = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad}× {self.variante} en {self.carrito}"


# ──────────────────────────────────────────────
#  Paso 2.1 — Modelos de Orden
# ──────────────────────────────────────────────

class Order(models.Model):
    class Estado(models.TextChoices):
        PENDING   = 'pending',   'Pendiente'
        PAID      = 'paid',      'Pagado'
        CANCELLED = 'cancelled', 'Cancelado'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDING,
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Orden'
        verbose_name_plural = 'Órdenes'

    def __str__(self):
        return f"Orden #{self.pk} — {self.usuario} [{self.get_estado_display()}]"


class OrderItem(models.Model):
    orden = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
    )
    # Referencia lazy — compatible aunque products aún no esté migrado
    variante = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.PROTECT,
    )
    cantidad = models.IntegerField()
    # Precio al momento de la compra (inmutable)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad}× {self.variante} @ ${self.precio_unitario}"
