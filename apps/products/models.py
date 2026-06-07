from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    """
    Representa una categoría de productos (ej: Remeras, Zapatillas).
    Se usa para organizar y filtrar productos en la tienda.
    """

    # Nombre visible de la categoría. Unique para evitar duplicados.
    nombre = models.CharField(max_length=100, unique=True)

    # Slug: versión URL-friendly del nombre (ej: "Remeras" → "remeras").
    # Se genera automáticamente en el método save(). Se usa en URLs amigables.
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    # Descripción opcional de la categoría.
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']  # Se listan alfabéticamente por defecto

    def save(self, *args, **kwargs):
        # Generamos el slug automáticamente solo si no tiene uno todavía.
        # Así el admin no necesita escribirlo a mano.
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Product(models.Model):
    """
    Representa un producto del catálogo (ej: Remera básica).
    Cada producto tiene un precio base; las variantes (talla/color)
    pueden sumarle un precio_extra encima de este base.
    """

    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)

    # Precio base del producto. Las variantes pueden tener precio_extra adicional.
    # max_digits=10, decimal_places=2 → soporta hasta 99,999,999.99
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)

    # Relación con Category. PROTECT evita borrar una categoría que tenga productos.
    categoria = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='productos'  # permite hacer categoria.productos.all()
    )

    # Imagen del producto. Pillow la procesa; se guarda en media/products/.
    # null=True / blank=True porque un producto puede cargarse sin imagen todavía.
    imagen = models.ImageField(upload_to='products/', blank=True, null=True)

    # Permite desactivar un producto sin borrarlo de la BD.
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    
class ProductVariant(models.Model):
    """
    Representa una variante específica de un producto (ej: Remera talla M, color Rojo).
    Se agrega ahora como modelo mínimo para que las FKs del Integrante 2
    (CartItem y OrderItem) no generen errores. Se completa en el módulo 1.4.
    """

    TALLA_CHOICES = [
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
    ]

    # Producto al que pertenece esta variante
    producto = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variantes'
    )

    talla = models.CharField(max_length=5, choices=TALLA_CHOICES)
    color = models.CharField(max_length=50)
    stock = models.IntegerField(default=0)

    # Precio adicional sobre el precio_base del producto.
    # Puede ser 0 si la variante no tiene costo extra.
    precio_extra = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.producto.nombre} - {self.talla} - {self.color}"
    