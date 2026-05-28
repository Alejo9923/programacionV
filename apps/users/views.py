"""
Las vistas son las que reciben la request HTTP, usan los serializers para validar los datos, y devuelven la response.
Es el "punto de entrada" de cada endpoint.
"""

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import RegisterSerializer, UserProfileSerializer


class RegisterView(APIView):
    """
    Endpoint: POST /api/auth/register/
    Crea un usuario nuevo y devuelve sus tokens JWT.
    """

    # AllowAny significa que cualquiera puede acceder a este endpoint,
    # incluso sin estar autenticado. Tiene sentido porque es el registro,
    # el usuario todavía no tiene token.
    permission_classes = [AllowAny]

    def post(self, request):
        # request.data contiene el JSON que mandó el cliente,
        # ya parseado como diccionario por DRF.
        serializer = RegisterSerializer(data=request.data)

        # is_valid() ejecuta todas las validaciones del serializer.
        # Si algo falla, is_valid() devuelve False y serializer.errors
        # contiene los mensajes de error.
        if serializer.is_valid():
            # save() llama internamente al método create() que definimos
            # en el serializer. Devuelve el objeto User recién creado.
            user = serializer.save()

            # Generamos los tokens JWT para el usuario recién creado.
            # refresh contiene ambos tokens: el refresh y el access.
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': RegisterSerializer(user).data,
                'refresh': str(refresh),
                # access_token es una propiedad del objeto refresh
                # que genera el token de corta duración.
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)  # 201 = recurso creado exitosamente

        # Si la validación falló, devolvemos los errores con 400.
        # 400 = Bad Request, el cliente mandó datos incorrectos.
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    Endpoint: POST /api/auth/logout/
    Invalida el refresh token para cerrar la sesión.
    """

    # IsAuthenticated significa que solo usuarios con un token JWT
    # válido en el header pueden acceder. Si no hay token, DRF
    # devuelve automáticamente un 401 Unauthorized.
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')

            # Si el cliente no mandó el refresh token en el body,
            # no podemos invalidarlo. Devolvemos error.
            if not refresh_token:
                return Response(
                    {'error': 'Se requiere el refresh token.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Creamos el objeto RefreshToken a partir del string
            # que mandó el cliente para poder manipularlo.
            token = RefreshToken(refresh_token)

            # blacklist() agrega este token a una tabla en la base de datos
            # de tokens inválidos. Aunque el token no haya expirado,
            # Django lo rechazará en cualquier request futura.
            token.blacklist()

            return Response(
                {'detail': 'Sesión cerrada correctamente.'},
                status=status.HTTP_200_OK
            )

        except TokenError:
            # TokenError ocurre si el string que mandaron no es un
            # refresh token válido, o si ya fue invalidado antes.
            return Response(
                {'error': 'Token inválido o ya expirado.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Endpoint: GET /api/auth/profile/   → ver perfil
              PATCH /api/auth/profile/ → editar perfil parcialmente
    """

    # Solo usuarios autenticados pueden ver o editar su perfil.
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        # get_object() le dice a Django QUÉ objeto mostrar o editar.
        # En lugar de buscar por ID en la URL, devolvemos directamente
        # al usuario que está haciendo la request.
        # request.user lo setea automáticamente DRF al validar el token JWT.
        return self.request.user