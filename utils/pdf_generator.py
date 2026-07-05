"""
utils/pdf_generator.py — Generador de facturas PDF.

Usa ReportLab (biblioteca estándar para PDFs en Python) para producir
facturas en memoria sin escribir nada en disco.

Función principal:
  generate_invoice(order) → bytes

La función recibe un objeto Order ya cargado con sus relaciones
(usuario, items → variante → producto) y devuelve los bytes del PDF
listos para ser enviados como respuesta HTTP o almacenados en un archivo.
"""

from io import BytesIO
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_invoice(order):
    """
    Genera la factura PDF de una Order y la retorna como bytes.

    Parámetros:
        order (Order): Instancia de Order con las relaciones
            'usuario', 'items__variante__producto' ya cargadas
            mediante select_related / prefetch_related en la vista.

    Retorna:
        bytes: Contenido completo del PDF listo para enviar como respuesta.

    Estructura del PDF:
        1. Encabezado — nombre de la tienda y fecha de emisión.
        2. Número de factura — formateado como FAC-00001.
        3. Datos del cliente — nombre completo y email.
        4. Tabla de ítems — Producto, Variante, Cantidad, P. Unitario, Subtotal.
        5. Total general.
    """

    # ── Buffer en memoria ──────────────────────────────────────────────────
    # BytesIO actúa como un archivo en RAM. ReportLab escribe el PDF aquí
    # y nunca toca el disco, lo que es más rápido y no requiere limpieza.
    buffer = BytesIO()

    # ── Documento base ─────────────────────────────────────────────────────
    # SimpleDocTemplate gestiona márgenes, tamaño de página y el flujo de
    # elementos (Paragraphs, Spacers, Tables) en el PDF.
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # ── Estilos ────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        'titulo',
        parent=styles['Title'],
        fontSize=22,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=4,
    )
    style_subtitle = ParagraphStyle(
        'subtitulo',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#555555'),
        spaceAfter=2,
    )
    style_label = ParagraphStyle(
        'etiqueta',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=2,
    )
    style_total = ParagraphStyle(
        'total',
        parent=styles['Normal'],
        fontSize=13,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=0,
    )

    # ── Lista de elementos del PDF ─────────────────────────────────────────
    # SimpleDocTemplate renderiza los elementos en orden, de arriba hacia abajo.
    elements = []

    # ── 1. Encabezado ──────────────────────────────────────────────────────
    elements.append(Paragraph("Mi E-commerce", style_title))
    elements.append(Paragraph(
        f"Fecha de emisión: {date.today().strftime('%d/%m/%Y')}",
        style_subtitle,
    ))
    elements.append(Spacer(1, 0.4 * cm))

    # ── 2. Número de factura ───────────────────────────────────────────────
    # :05d formatea el ID con ceros a la izquierda hasta 5 dígitos.
    # Ej: order.id = 3 → "FAC-00003"
    numero_factura = f"FAC-{order.id:05d}"
    elements.append(Paragraph(f"<b>Factura N°:</b> {numero_factura}", style_label))
    elements.append(Spacer(1, 0.3 * cm))

    # ── 3. Datos del cliente ───────────────────────────────────────────────
    usuario = order.usuario
    nombre_completo = f"{usuario.first_name} {usuario.last_name}".strip() or usuario.email
    elements.append(Paragraph("<b>Datos del cliente</b>", style_label))
    elements.append(Paragraph(f"Nombre: {nombre_completo}", style_label))
    elements.append(Paragraph(f"Email: {usuario.email}", style_label))
    elements.append(Spacer(1, 0.5 * cm))

    # ── 4. Tabla de ítems ──────────────────────────────────────────────────
    # La primera fila es el encabezado de la tabla.
    tabla_datos = [
        ["Producto", "Variante", "Cant.", "P. Unitario", "Subtotal"],
    ]

    for item in order.items.all():
        # Nombre del producto: item.variante.producto.nombre
        # La relación ya está precargada con prefetch_related en la vista,
        # así que este acceso no genera una query adicional a la BD.
        nombre_producto = item.variante.producto.nombre

        # Variante mostrada como "talla / color" (ej: "M / Rojo")
        variante_str = f"{item.variante.talla} / {item.variante.color}"

        # Subtotal de la línea = precio snapshot × cantidad
        subtotal = item.precio_unitario * item.cantidad

        tabla_datos.append([
            nombre_producto,
            variante_str,
            str(item.cantidad),
            f"${item.precio_unitario:,.2f}",
            f"${subtotal:,.2f}",
        ])

    tabla = Table(
        tabla_datos,
        # Anchos de columna ajustados al contenido esperado
        colWidths=[5 * cm, 3.5 * cm, 1.5 * cm, 3 * cm, 3 * cm],
        repeatRows=1,  # Repite la fila de encabezado si la tabla ocupa varias páginas
    )

    tabla.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND',   (0, 0), (-1, 0),  colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR',    (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',     (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, 0),  10),
        ('ALIGN',        (0, 0), (-1, 0),  'CENTER'),
        ('BOTTOMPADDING',(0, 0), (-1, 0),  8),
        ('TOPPADDING',   (0, 0), (-1, 0),  8),
        # Filas de datos
        ('BACKGROUND',   (0, 1), (-1, -1), colors.HexColor('#f7f7f7')),
        ('ROWBACKGROUNDS',(0, 1),(-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
        ('FONTNAME',     (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',     (0, 1), (-1, -1), 9),
        ('ALIGN',        (2, 1), (-1, -1), 'RIGHT'),   # Cant., precios alineados a la derecha
        ('ALIGN',        (0, 1), (1, -1),  'LEFT'),
        ('TOPPADDING',   (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING',(0, 1), (-1, -1), 6),
        # Bordes
        ('GRID',         (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('BOX',          (0, 0), (-1, -1), 1,   colors.HexColor('#1a1a2e')),
    ]))

    elements.append(tabla)
    elements.append(Spacer(1, 0.5 * cm))

    # ── 5. Total general ───────────────────────────────────────────────────
    # Se usa el campo order.total (calculado al momento del checkout),
    # no la suma de los subtotales de las filas, para evitar discrepancias
    # por redondeo de decimales.
    elements.append(Paragraph(
        f"<b>Total: ${order.total:,.2f}</b>",
        style_total,
    ))

    # ── Construir el PDF ───────────────────────────────────────────────────
    # doc.build() renderiza todos los elementos y escribe el PDF en el buffer.
    doc.build(elements)

    # Retornamos los bytes del PDF. El buffer queda en memoria hasta que
    # Python lo recolecte; no hay archivos temporales que limpiar.
    return buffer.getvalue()
