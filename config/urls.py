from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Panel de administración que viene incluido en Django.
    # Permite gestionar toda la base de datos desde el navegador.
    path('admin/', admin.site.urls),

    # include() le dice a Django: "todo lo que empiece con api/auth/
    # derivalo al archivo apps/users/urls.py para que lo resuelva".
    # Así cada app maneja sus propias URLs y config/urls.py
    # solo actúa como distribuidor principal.
    path('api/auth/', include('apps.users.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# static() habilita que Django sirva las imágenes subidas (como fotos
# de productos). Solo funciona en desarrollo (DEBUG=True).
# En producción esto lo manejaría un servidor como Nginx.