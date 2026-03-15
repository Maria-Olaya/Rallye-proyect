# scheduling/services.py

from datetime import datetime, timedelta, date
from scheduling.models import Cita
from core.models import Local


def citas_por_dia(local: Local) -> int:
    apertura = local.hora_apertura.hour * 60 + local.hora_apertura.minute
    cierre = local.hora_cierre.hour * 60 + local.hora_cierre.minute
    slots = (cierre - apertura) // 120
    return slots * local.num_mecanicos


def generar_citas_para_local(local: Local, fecha: date) -> list[Cita]:
    # Si ya hay citas para ese local y fecha, no generamos nada
    if Cita.objects.filter(local=local, fecha=fecha).exists():
        return []

    apertura = datetime.combine(fecha, local.hora_apertura)
    cierre = datetime.combine(fecha, local.hora_cierre)
    slot_duration = timedelta(hours=2)

    citas_creadas = []
    hora_actual = apertura

    while hora_actual + slot_duration <= cierre:
        hora_fin = hora_actual + slot_duration
        for _ in range(local.num_mecanicos):
            cita = Cita.objects.create(
                local=local,
                fecha=fecha,
                hora_inicio=hora_actual.time(),
                hora_fin=hora_fin.time(),
                estado=Cita.Estado.LIBRE,
            )
            citas_creadas.append(cita)
        hora_actual += slot_duration

    return citas_creadas
