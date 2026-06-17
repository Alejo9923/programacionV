# programacionV
## Fundamento para la elección del Tema
Las principales razones por la que eleí este tema sobre los demás posibles es debido a que:
- En mi día a día veo e interactuo con tiendas online que dejan mucho que desear, y me gustaría comprobar si soy capaz de desarrollar una yo mismo sin las falencias que suelo encontrar en las que me disgustan.
- Django, como framework de Python, ofrece las herramientas necesarias para construir este tipo de sistema de forma estructurada y escalable. Este proyecto representa un desafío técnico equilibrado entre los conceptos mencionados en clase y los requeridos entre los posibles temas mencionados.

## Stack Tecnológico

- Python 3.12
- Django 5.x
- Django REST Framework
- SQLite (desarrollo) → PostgreSQL (producción, paso final)
- djangorestframework-simplejwt (autenticación JWT)
- django-filter (filtrado de productos)
- Pillow (procesamiento de imágenes)
- ASGI con Uvicorn

## Justificación: ASGI sobre WSGI

Este proyecto utiliza **ASGI** (Asynchronous Server Gateway Interface) en lugar de WSGI como estándar de servidor.

**Motivo:** un e-commerce recibe múltiples requests simultáneos (navegación, búsquedas, checkout, validación de stock). WSGI es síncrono y bloquea el servidor mientras procesa una tarea pesada; ASGI permite atender otras requests mientras espera respuesta de la base de datos, sin bloquear. Django 5.x tiene soporte nativo para vistas asíncronas, lo cual es aprovechable bajo ASGI.

El archivo `config/asgi.py` ya viene generado por Django y fue verificado corriendo el proyecto con Uvicorn:

```bash
python -m uvicorn config.asgi:application --reload
```

En producción se usaría:

```bash
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

**Nota sobre WebSockets:** la elección de ASGI no implica que el proyecto implemente WebSockets. A la fecha, el proyecto **no implementa WebSockets** porque está fuera del alcance establecido (ver sección de alcance). Implementarlos requeriría agregar Django Channels, un `routing.py`, consumers asíncronos y un channel layer (Redis), lo cual excede el núcleo funcional definido para esta entrega.

## Estructura del Proyecto

programacionV/

├── manage.py

├── requirements.txt

├── .env                  # Credenciales reales — NO se sube a Git

├── .env.example           # Plantilla vacía — sí se sube a Git

├── .gitignore

│

├── config/                # Configuración central del proyecto

│   ├── settings.py

│   ├── urls.py

│   ├── wsgi.py

│   └── asgi.py

│

├── apps/

│   ├── users/              # Integrante 1 — autenticación JWT

│   ├── products/           # Integrante 1 — categorías, productos, variantes

│   ├── orders/              # Integrante 1 (carrito) + Integrante 2 (órdenes)

│   ├── reviews/             # Integrante 2 — reseñas con rating

│   └── web/                  # Integrante 1 — interfaz web (Django Templates)

│

└── templates/

└── web/                 # Templates HTML de la interfaz web

## Alcance del Proyecto

### Dentro del alcance — implementado

- Autenticación JWT (register, login, logout, perfil)
- Categorías y productos con permisos por rol y filtros
- Variantes de producto (talla, color, stock)
- Carrito de compras con validación de stock
- Checkout y confirmación simulada de pago
- Historial de órdenes *(en curso — depende del Integrante 2)*
- Reseñas con rating
- Interfaz web con Django Templates
- Seguridad: CSRF, XSS, Clickjacking, SQL Injection
- Justificación y verificación de ASGI

### Fuera del alcance — opcional si sobra tiempo

- Cupones de descuento
- Integración real con MercadoPago
- Facturas en PDF
- Migración a PostgreSQL (último paso antes de la entrega)