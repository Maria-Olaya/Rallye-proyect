from django.db import models
from django.conf import settings
from core.models import Sede


class Jornada(models.Model):
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name="jornadas")
    dia_semana = models.IntegerField()  # 0 lunes ... 6 domingo
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activa = models.BooleanField(default=True)


class Cita(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE"
        CONFIRMADA = "CONFIRMADA"
        CANCELADA = "CANCELADA"
        ATENDIDA = "ATENDIDA"

    sede = models.ForeignKey(Sede, on_delete=models.PROTECT, related_name="citas")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="citas")
    fecha_hora = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    motivo_cancelacion = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
