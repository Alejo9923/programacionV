"""
Las URLs son el "mapa" que conecta cada dirección web con su vista correspondiente.
Cuando llega una request a /api/auth/register/, Django consulta este archivo para saber qué vista debe manejarla.
"""

from django.urls import path

# TokenObtainPairView maneja el login: recibe email + password
# y devuelve los tokens access y refresh. Ya viene lista en simplejwt.
# TokenRefreshView maneja la renovación del access token usando
# el refresh token, cuando el access token expira.
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Importamos las vistas que creamos
from .views import RegisterView, LogoutView, ProfileView

urlpatterns = [
    # POST /api/auth/register/ → crea usuario y devuelve tokens
    path('register/', RegisterView.as_view(), name='auth-register'),

    # POST /api/auth/login/ → recibe email+password, devuelve tokens
    # Usamos TokenObtainPairView directamente sin crear una vista propia.
    path('login/', TokenObtainPairView.as_view(), name='auth-login'),

    # POST /api/auth/login/refresh/ → renueva el access token
    # El cliente manda el refresh token y recibe un access token nuevo.
    # Esto evita pedirle al usuario que haga login cada hora.
    path('login/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # POST /api/auth/logout/ → invalida el refresh token
    path('logout/', LogoutView.as_view(), name='auth-logout'),

    # GET  /api/auth/profile/ → ver datos del usuario autenticado
    # PATCH /api/auth/profile/ → editar datos del usuario autenticado
    path('profile/', ProfileView.as_view(), name='auth-profile'),
]