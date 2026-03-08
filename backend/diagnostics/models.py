from django.db import models
from scheduling.models import Cita

class Diagnostico(models.Model):
    cita = models.OneToOneField(Cita, on_delete=models.CASCADE, related_name="diagnostico")
    descripcion = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Radicado(models.Model):
    diagnostico = models.OneToOneField(Diagnostico, on_delete=models.CASCADE, related_name="radicado")
    codigo = models.CharField(max_length=30, unique=True)
    enviado = models.BooleanField(default=False)
    enviado_at = models.DateTimeField(null=True, blank=True)

class Evidencia(models.Model):
    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE, related_name="evidencias")
    # por ahora solo guardamos url o texto (luego puedes pasar a FileField)
    archivo_url = models.URLField(blank=True, default="")
    nota = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
