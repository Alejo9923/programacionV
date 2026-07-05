from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.views.static import serve
from django.conf import settings

urlpatterns = [
    # Panel de administración que viene incluido en Django.
    # Permite gestionar toda la base de datos desde el navegador.
    path('admin/', admin.site.urls),
    # Redirige la raíz del sitio al login web, ya que no hay una home propia del proyecto.
    path('', RedirectView.as_view(url='/web/login/', permanent=False), name='home'),


    # include() le dice a Django: "todo lo que empiece con api/auth/
    # derivalo al archivo apps/users/urls.py para que lo resuelva".
    # Así cada app maneja sus propias URLs y config/urls.py
    # solo actúa como distribuidor principal.
    path('api/auth/', include('apps.users.urls')),
    path('api/', include('apps.products.urls')),
    path('api/', include('apps.orders.urls')),
    path('api/', include('apps.reviews.urls')),  # Reseñas — Paso 2.5
    path('web/', include('apps.web.urls')),

    # Servimos media/ (imágenes de producto) y static/ (admin, DRF browsable
    # API) directamente desde Django, sin Nginx/S3 delante. A diferencia del
    # helper static() —que solo agrega estas rutas si DEBUG=True—,
    # django.views.static.serve funciona igual con DEBUG=False. No es lo ideal
    # a gran escala, pero alcanza para un proyecto de esta envergadura.
    # STATIC_ROOT se llena con `python manage.py collectstatic` antes de
    # levantar el server en producción (ver README).
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]