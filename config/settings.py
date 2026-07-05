from datetime import timedelta  # agregar al inicio del archivo
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')

# En producción DEBUG debe ser False: con True, Django expone tracebacks
# completos (código fuente, variables, configuración) ante cualquier error.
DEBUG = config('DEBUG', default=False, cast=bool)

# Hosts/dominios permitidos, separados por coma en la variable de entorno
# (ej. "midominio.com,www.midominio.com"). Si DEBUG=True y no se define
# nada, Django igual permite localhost/127.0.0.1 automáticamente.
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
]

LOCAL_APPS = [
    'apps.users',
    'apps.products',
    'apps.orders',
    'apps.reviews',
    'apps.web',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-py'
TIME_ZONE = 'America/Asuncion'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
# Carpeta donde `collectstatic` junta los estáticos (admin, DRF browsable API,
# etc.) para servirlos en producción, donde DEBUG=False y Django ya no los
# sirve automáticamente. Ver config/urls.py para cómo se sirven sin DEBUG.
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Modelo de usuario personalizado.
# Django usa esta configuración en TODA la aplicación para saber
# qué modelo representa a un usuario.
AUTH_USER_MODEL = 'users.User'


# Configuración global de DRF.
# Define el comportamiento por defecto para TODOS los endpoints.
REST_FRAMEWORK = {
    # Usamos JWT para autenticar. DRF leerá el header
    # Authorization: Bearer  en cada request.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Por defecto todos los endpoints requieren autenticación.
    # Las vistas con AllowAny sobreescriben esto individualmente.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
}

# Configuración específica de los tokens JWT.
SIMPLE_JWT = {
    # El access token dura 1 hora. Es el token que se manda
    # en cada request para autenticarse.
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),

    # El refresh token dura 7 días. Solo se usa para pedir
    # un access token nuevo cuando el anterior expiró.
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # Cada vez que se usa el refresh token, se genera uno nuevo.
    # Esto extiende la sesión automáticamente mientras el usuario esté activo.
    'ROTATE_REFRESH_TOKENS': True,

    # Cuando se rota el refresh token, el anterior se agrega
    # a la blacklist para que no pueda usarse de nuevo.
    'BLACKLIST_AFTER_ROTATION': True,

    # Formato del header de autenticación: Authorization: Bearer 
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Protección contra Clickjacking — impide que la página sea incrustada en un iframe
# de otro sitio. XFrameOptionsMiddleware (ya activo en MIDDLEWARE) lee esta variable.
X_FRAME_OPTIONS = 'DENY'