from django.conf import settings
from django.db import models


class Diagnostico(models.Model):
    cita = models.OneToOneField("scheduling.Cita", on_delete=models.CASCADE, related_name="diagnostico")
    descripcion = models.TextField()
    radicado = models.CharField(max_length=30, unique=True, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="diagnosticos_registrados",
        null=True,
        blank=True,
    )
    correo_radicado_enviado = models.BooleanField(default=False)
    fecha_envio_radicado = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"{self.radicado} - {self.cita.placa_moto}"


class Evidencia(models.Model):
    diagnostico = models.ForeignKey("Diagnostico", on_delete=models.CASCADE, related_name="evidencias")
    archivo_url = models.URLField(blank=True, default="")
    nota = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)


class Radicado(models.Model):
    diagnostico = models.OneToOneField("Diagnostico", on_delete=models.CASCADE, related_name="radicado_legacy")
    codigo = models.CharField(max_length=30, unique=True)
    enviado = models.BooleanField(default=False)
    enviado_at = models.DateTimeField(null=True, blank=True)
