from django.db import models

from core.models import Local


class Cita(models.Model):
    class Estado(models.TextChoices):
        LIBRE = "LIBRE", "Libre"
        ASIGNADA = "ASIGNADA", "Asignada"

    class TipoServicio(models.TextChoices):
        MANTENIMIENTO = "MANTENIMIENTO", "Mantenimiento General"
        REVISION = "REVISION", "Revisión General"
        ALISTAMIENTO = "ALISTAMIENTO", "Alistamiento"
        GARANTIA = "GARANTIA", "Revisión por Garantía"

    local = models.ForeignKey(Local, on_delete=models.PROTECT, related_name="citas")
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.LIBRE)

    # Datos del cliente — null mientras la cita está LIBRE
    tipo_servicio = models.CharField(max_length=20, choices=TipoServicio.choices, null=True, blank=True)
    cliente_nombre = models.CharField(max_length=120, blank=True, default="")
    cliente_documento = models.CharField(max_length=20, blank=True, default="")
    cliente_telefono = models.CharField(max_length=20, blank=True, default="")
    cliente_correo = models.EmailField(blank=True, default="")
    placa_moto = models.CharField(max_length=10, blank=True, default="")
    referencia_moto = models.CharField(max_length=60, blank=True, default="")

    class Meta:
        ordering = ["fecha", "hora_inicio"]

    def __str__(self):
        return f"{self.local} | {self.fecha} {self.hora_inicio}-{self.hora_fin} | {self.estado}"
