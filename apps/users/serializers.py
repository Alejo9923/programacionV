"""
Los serializers son el "traductor" entre los datos que llegan por HTTP (JSON) y los objetos de Python/Django.
También son donde se valida que los datos sean correctos antes de tocar la base de datos.

El concepto clave es la validación en cadena. Cuando llega una request de registro, DRF ejecuta en orden:
1- validate_email() — verifica que el email sea único
2- validate() — verifica que las dos contraseñas coincidan
3- create() — recién si todo está bien, crea el usuario

Si cualquiera de esos pasos falla, Django devuelve un 400 Bad Request con el mensaje de error y nunca toca la base de datos
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

# get_user_model() devuelve el modelo de usuario activo en el proyecto.
# Es mejor práctica que importar User directamente, porque respeta
# lo que definimos en AUTH_USER_MODEL dentro de settings.py.
User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    # write_only=True significa que este campo se recibe pero NUNCA
    # se devuelve en la respuesta. Así la contraseña nunca viaja de vuelta.
    password = serializers.CharField(write_only=True, min_length=8)

    # Campo extra para confirmar que el usuario escribió bien su contraseña.
    # No existe en el modelo, solo lo usamos para validar.
    password2 = serializers.CharField(write_only=True, label='Confirmar contraseña')

    class Meta:
        # Le decimos a DRF que este serializer está basado en el modelo User.
        model = User
        # Solo exponemos estos campos. Cualquier otro campo del modelo
        # (como is_staff, last_login, etc.) queda oculto.
        fields = ['id', 'username', 'email', 'password', 'password2', 'phone', 'address']

    def validate_email(self, value):
        # Los métodos validate_ se ejecutan automáticamente por DRF
        # cuando llega una request. Este verifica que el email no esté en uso.
        # Si lanzamos ValidationError, DRF devuelve un 400 con el mensaje.
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Ya existe un usuario con este email.')
        return value

    def validate(self, data):
        # validate() sin nombre de campo valida el objeto completo.
        # Se ejecuta después de validar cada campo individualmente.
        # Acá comparamos los dos campos de contraseña entre sí.
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password2': 'Las contraseñas no coinciden.'})
        return data

    def create(self, validated_data):
        # validated_data ya pasó todas las validaciones de arriba.
        # Removemos password2 porque no es un campo del modelo User.
        validated_data.pop('password2')

        # create_user() es un método de Django que hashea la contraseña
        # antes de guardarla. NUNCA usar User.objects.create() directamente
        # para crear usuarios porque guardaría la contraseña en texto plano.
        #Adicionalmente, los asteriscos en "**validated_data" sirve para desempaquetar un diccionario como argumentos nombrados  
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    # Este serializer es más simple: solo se usa para leer y editar
    # el perfil del usuario ya autenticado. No necesita validar contraseñas.
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'address', 'date_joined']

        # read_only_fields son campos que se muestran pero no se pueden
        # modificar. El id y la fecha de registro no deben cambiarse.
        read_only_fields = ['id', 'date_joined']