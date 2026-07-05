# programacionV
## Fundamento para la elección del Tema
Las principales razones por la que eleí este tema sobre los demás posibles es debido a que:
- En mi día a día veo e interactuo con tiendas online que dejan mucho que desear, y me gustaría comprobar si soy capaz de desarrollar una yo mismo sin las falencias que suelo encontrar en las que me disgustan.
- Django, como framework de Python, ofrece las herramientas necesarias para construir este tipo de sistema de forma estructurada y escalable. Este proyecto representa un desafío técnico equilibrado entre los conceptos mencionados en clase y los requeridos entre los posibles temas mencionados.

## Stack Tecnológico

- Python 3.12
- Django 6.x
- Django REST Framework
- SQLite (desarrollo y producción — alcanza para el volumen de este proyecto)
- djangorestframework-simplejwt (autenticación JWT)
- django-filter (filtrado de productos)
- Pillow (procesamiento de imágenes)
- ReportLab (generación de facturas PDF)
- ASGI con Uvicorn

## Justificación: ASGI sobre WSGI

Este proyecto utiliza **ASGI** (Asynchronous Server Gateway Interface) en lugar de WSGI como estándar de servidor.

**Motivo:** un e-commerce recibe múltiples requests simultáneos (navegación, búsquedas, checkout, validación de stock). WSGI es síncrono y bloquea el servidor mientras procesa una tarea pesada; ASGI permite atender otras requests mientras espera respuesta de la base de datos, sin bloquear. Django 6.x tiene soporte nativo para vistas asíncronas, lo cual es aprovechable bajo ASGI.

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
- Historial y detalle de órdenes
- Reseñas con rating (1-5, solo compradores)
- Factura en PDF (ReportLab) para órdenes confirmadas
- Interfaz web con Django Templates, consumiendo la propia API REST
- Seguridad: CSRF, XSS, Clickjacking, SQL Injection
- Justificación y verificación de ASGI

### Fuera del alcance

Confirmado con el docente que no es necesario para esta entrega:

- Cupones de descuento
- Integración real con MercadoPago (el pago se simula: el checkout crea la
  orden y un endpoint aparte la confirma, pensado para poder enchufar un
  webhook real más adelante sin refactor)
- WebSockets / Django Channels
- Redis y Celery (tareas asíncronas)
- PostgreSQL — el proyecto usa SQLite tanto en desarrollo como en producción

## Puesta en marcha

```bash
git clone <url-del-repo>
cd programacionV
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / Mac

pip install -r requirements.txt

copy .env.example .env         # Windows
# cp .env.example .env         # Linux / Mac
# Completar SECRET_KEY en .env (ver instrucciones dentro del archivo)

python manage.py migrate
python manage.py createsuperuser   # opcional, para entrar al /admin/
```

### Correr en desarrollo

Con `DEBUG=True` en `.env`:

```bash
python manage.py runserver
```

### Correr en modo producción (DEBUG=False)

`.env.example` ya trae `DEBUG=False` por defecto. Antes de levantar el
servidor hace falta juntar los archivos estáticos (admin, DRF browsable API)
en `STATIC_ROOT`, porque con `DEBUG=False` Django deja de servirlos solo:

```bash
python manage.py collectstatic --noinput
python -m uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

`ALLOWED_HOSTS` (en `.env`) debe incluir el dominio o IP real donde se
despliega la app; con el valor por defecto (`127.0.0.1,localhost`) solo
funciona en la propia máquina.