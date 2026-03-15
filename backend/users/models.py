from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Modelo de usuario para Rallye Motor's.

    Tipos de usuario:
        - superuser (is_superuser=True): programadores, acceso total a /admin/
        - admin_rallye (is_superuser=False): administrador de local,
          inicia sesión con correo corporativo, accede al dashboard.

    El login se realiza con email en lugar de username.
    Cada admin_rallye tiene asignado un local específico.
    """

    email = models.EmailField(unique=True)
    local = models.ForeignKey(
        "core.Local",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="administradores",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Administrador"
        verbose_name_plural = "Administradores"

    def __str__(self):
        return self.email

    @property
    def es_admin_rallye(self):
        return self.is_active and not self.is_superuser
