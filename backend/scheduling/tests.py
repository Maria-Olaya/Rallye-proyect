# scheduling/tests.py

from datetime import date, time
from django.test import TestCase

from core.models import Local, Sede, Municipio
from scheduling.models import Cita
from scheduling.services import citas_por_dia, generar_citas_para_local


def make_local(hora_apertura, hora_cierre, num_mecanicos, nombre="TestLocal"):
    municipio = Municipio.objects.create(nombre="TestMunicipio", departamento="TestDepto")
    sede = Sede.objects.create(nombre="TestSede", direccion="Calle 1", municipio=municipio)
    return Local.objects.create(
        nombre=nombre,
        sede=sede,
        direccion="Calle 2",
        telefono="3001234567",
        correo_admin="admin@test.com",
        hora_apertura=hora_apertura,
        hora_cierre=hora_cierre,
        num_mecanicos=num_mecanicos,
    )


# ─────────────────────────────────────────
# citas_por_dia
# ─────────────────────────────────────────


class CitasPorDiaTest(TestCase):
    def test_caso_base(self):
        """6am-6pm, 3 mecánicos → 6 slots × 3 = 18"""
        local = make_local(time(6, 0), time(18, 0), 3)
        self.assertEqual(citas_por_dia(local), 18)

    def test_horario_corto(self):
        """8am-12pm, 1 mecánico → 2 slots × 1 = 2"""
        local = make_local(time(8, 0), time(12, 0), 1)
        self.assertEqual(citas_por_dia(local), 2)

    def test_un_solo_slot(self):
        """8am-10am, 2 mecánicos → 1 slot × 2 = 2"""
        local = make_local(time(8, 0), time(10, 0), 2)
        self.assertEqual(citas_por_dia(local), 2)

    def test_muchos_mecanicos(self):
        """6am-6pm, 10 mecánicos → 6 slots × 10 = 60"""
        local = make_local(time(6, 0), time(18, 0), 10)
        self.assertEqual(citas_por_dia(local), 60)

    def test_hora_sobrante_se_ignora(self):
        """6am-7pm = 13h → 6 slots completos × 3 mec = 18 (la hora sobrante se ignora)"""
        local = make_local(time(6, 0), time(19, 0), 3)
        self.assertEqual(citas_por_dia(local), 18)

    def test_un_mecanico_dia_completo(self):
        """6am-6pm, 1 mecánico → 6 slots × 1 = 6"""
        local = make_local(time(6, 0), time(18, 0), 1)
        self.assertEqual(citas_por_dia(local), 6)

    def test_dos_mecanicos(self):
        """8am-4pm, 2 mecánicos → 4 slots × 2 = 8"""
        local = make_local(time(8, 0), time(16, 0), 2)
        self.assertEqual(citas_por_dia(local), 8)

    def test_horario_tarde(self):
        """12pm-8pm, 1 mecánico → 4 slots × 1 = 4"""
        local = make_local(time(12, 0), time(20, 0), 1)
        self.assertEqual(citas_por_dia(local), 4)

    def test_exactamente_dos_horas(self):
        """10am-12pm, 5 mecánicos → 1 slot × 5 = 5"""
        local = make_local(time(10, 0), time(12, 0), 5)
        self.assertEqual(citas_por_dia(local), 5)

    def test_horario_con_minutos_sobrantes(self):
        """8am-11:30am = 3.5h → 1 slot completo × 2 mec = 2"""
        local = make_local(time(8, 0), time(11, 30), 2)
        self.assertEqual(citas_por_dia(local), 2)


# ─────────────────────────────────────────
# generar_citas_para_local
# ─────────────────────────────────────────


class GenerarCitasTest(TestCase):
    def test_genera_cantidad_correcta(self):
        """6am-10am, 2 mecánicos → 2 slots × 2 mec = 4 citas"""
        local = make_local(time(6, 0), time(10, 0), 2)
        citas = generar_citas_para_local(local, date(2025, 1, 15))
        self.assertEqual(len(citas), 4)
        self.assertEqual(Cita.objects.count(), 4)

    def test_todas_en_estado_libre(self):
        """Todas las citas generadas deben estar LIBRE"""
        local = make_local(time(6, 0), time(10, 0), 2)
        generar_citas_para_local(local, date(2025, 1, 15))
        self.assertEqual(Cita.objects.filter(estado=Cita.Estado.LIBRE).count(), 4)

    def test_ninguna_en_estado_asignada(self):
        """No debe haber ninguna ASIGNADA al generar"""
        local = make_local(time(6, 0), time(10, 0), 2)
        generar_citas_para_local(local, date(2025, 1, 15))
        self.assertEqual(Cita.objects.filter(estado=Cita.Estado.ASIGNADA).count(), 0)

    def test_no_duplica_segunda_llamada(self):
        """Segunda llamada con mismo local y fecha retorna lista vacía"""
        local = make_local(time(6, 0), time(10, 0), 1)
        primera = generar_citas_para_local(local, date(2025, 1, 15))
        segunda = generar_citas_para_local(local, date(2025, 1, 15))
        self.assertEqual(len(primera), 2)
        self.assertEqual(len(segunda), 0)
        self.assertEqual(Cita.objects.count(), 2)

    def test_slots_en_orden_correcto(self):
        """6am-10am, 1 mecánico → slots 6-8 y 8-10 en orden"""
        local = make_local(time(6, 0), time(10, 0), 1)
        generar_citas_para_local(local, date(2025, 1, 15))
        citas = list(Cita.objects.all())
        self.assertEqual(citas[0].hora_inicio, time(6, 0))
        self.assertEqual(citas[0].hora_fin, time(8, 0))
        self.assertEqual(citas[1].hora_inicio, time(8, 0))
        self.assertEqual(citas[1].hora_fin, time(10, 0))

    def test_no_genera_slot_fuera_del_cierre(self):
        """6am-9am → solo slot 6-8, el 8-10 se pasa del cierre"""
        local = make_local(time(6, 0), time(9, 0), 1)
        citas = generar_citas_para_local(local, date(2025, 1, 15))
        self.assertEqual(len(citas), 1)
        self.assertEqual(citas[0].hora_inicio, time(6, 0))
        self.assertEqual(citas[0].hora_fin, time(8, 0))

    def test_fechas_diferentes_son_independientes(self):
        """Mismo local, fechas distintas → citas independientes, no se bloquean"""
        local = make_local(time(6, 0), time(10, 0), 1)
        d1 = generar_citas_para_local(local, date(2025, 1, 15))
        d2 = generar_citas_para_local(local, date(2025, 1, 16))
        self.assertEqual(len(d1), 2)
        self.assertEqual(len(d2), 2)
        self.assertEqual(Cita.objects.count(), 4)

    def test_dos_locales_no_se_mezclan(self):
        """Dos locales distintos no comparten citas"""
        local1 = make_local(time(6, 0), time(10, 0), 1, nombre="Local1")
        local2 = make_local(time(6, 0), time(10, 0), 1, nombre="Local2")
        generar_citas_para_local(local1, date(2025, 1, 15))
        generar_citas_para_local(local2, date(2025, 1, 15))
        self.assertEqual(Cita.objects.filter(local=local1).count(), 2)
        self.assertEqual(Cita.objects.filter(local=local2).count(), 2)

    def test_horario_completo_18_citas(self):
        """6am-6pm, 3 mecánicos → 18 citas en DB"""
        local = make_local(time(6, 0), time(18, 0), 3)
        citas = generar_citas_para_local(local, date(2025, 1, 15))
        self.assertEqual(len(citas), 18)
        self.assertEqual(Cita.objects.count(), 18)

    def test_local_asociado_correctamente(self):
        """Todas las citas deben pertenecer al local correcto"""
        local = make_local(time(6, 0), time(10, 0), 2)
        generar_citas_para_local(local, date(2025, 1, 15))
        self.assertEqual(Cita.objects.filter(local=local).count(), 4)

    def test_fecha_asociada_correctamente(self):
        """Todas las citas deben tener la fecha correcta"""
        local = make_local(time(6, 0), time(10, 0), 1)
        fecha = date(2025, 6, 20)
        generar_citas_para_local(local, fecha)
        self.assertTrue(Cita.objects.filter(fecha=fecha).exists())
        self.assertFalse(Cita.objects.exclude(fecha=fecha).exists())

    def test_hora_fin_siempre_dos_horas_despues(self):
        """En todos los slots, hora_fin debe ser exactamente hora_inicio + 2h"""
        local = make_local(time(6, 0), time(18, 0), 1)
        generar_citas_para_local(local, date(2025, 1, 15))
        for cita in Cita.objects.all():
            diff = (cita.hora_fin.hour * 60 + cita.hora_fin.minute) - (
                cita.hora_inicio.hour * 60 + cita.hora_inicio.minute
            )
            self.assertEqual(diff, 120)

    def test_multiples_mecanicos_mismo_slot_misma_hora(self):
        """Con 3 mecánicos, deben haber 3 citas con la misma hora_inicio"""
        local = make_local(time(8, 0), time(10, 0), 3)
        generar_citas_para_local(local, date(2025, 1, 15))
        self.assertEqual(Cita.objects.filter(hora_inicio=time(8, 0)).count(), 3)
