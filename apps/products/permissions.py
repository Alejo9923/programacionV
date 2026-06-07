from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    Permiso personalizado para el catálogo de productos y categorías.

    Lógica:
    - Cualquier usuario (incluso sin autenticar) puede hacer GET, HEAD, OPTIONS
      → son los llamados SAFE_METHODS, no modifican datos.
    - Solo usuarios con is_staff=True (administradores) pueden hacer
      POST, PUT, PATCH, DELETE → crear, editar o borrar productos/categorías.

    Se crea como clase separada (en lugar de usar IsAdminUser de DRF)
    para tener control explícito y poder extenderla fácilmente en el futuro.
    """

    def has_permission(self, request, view):
        # Si el método es de solo lectura, permitir a cualquiera
        if request.method in SAFE_METHODS:
            return True

        # Para cualquier otra operación, exigir autenticación y rol admin
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )