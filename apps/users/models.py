# AbstractUser es el modelo de usuario que ya trae Django listo.
# En lugar de crearlo desde cero, lo "extendemos" para agregarle
# campos extra sin perder todo lo que Django ya maneja:
# password, username, email, is_active, date_joined, etc.
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Hacemos que el email sea ÚNICO en la base de datos.
    # Sin unique=True, dos usuarios podrían registrarse con el mismo email.
    email = models.EmailField(unique=True)

    # Campos extra que el proyecto requiere.
    # blank=True significa que son opcionales al crear el usuario.
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    # Le decimos a Django que el "nombre de usuario" para login es el email,
    # no el campo username que trae por defecto.
    # Esto afecta también a los tokens JWT: pedirán email + password.
    USERNAME_FIELD = 'email'

    # Campos que se piden al crear un superusuario por consola (createsuperuser).
    # username sigue existiendo pero ya no es el campo principal de login.
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        # Representación legible del objeto cuando se muestra en el admin
        # o en un print(). Sin esto Django mostraría "User object (1)".
        return self.email