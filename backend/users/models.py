from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Modelo de usuario para administradores de Rallye Motor's.

    Los usuarios son creados exclusivamente por superusers desde /admin/.
    No existe registro público. Todos los usuarios autenticados son
    administradores del sistema.

    Hereda de AbstractUser:
        - username (obligatorio, único)
        - password (encriptado con PBKDF2)
        - is_active
        - is_staff
        - is_superuser
        - date_joined
    """

    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"

    def __str__(self):
        return self.username
