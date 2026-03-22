from django.utils import timezone

from diagnostics.models import Diagnostico


def generar_radicado() -> str:
    base = timezone.localtime().strftime("RAD-%Y%m%d-%H%M%S")
    sufijo = 1
    codigo = f"{base}-{sufijo:02d}"
    while Diagnostico.objects.filter(radicado=codigo).exists():
        sufijo += 1
        codigo = f"{base}-{sufijo:02d}"
    return codigo
