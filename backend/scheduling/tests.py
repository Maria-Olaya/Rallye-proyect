# scheduling/tests.py

from datetime import date, time

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Local, Municipio, Sede
from scheduling.models import Cita
from scheduling.services import (
    citas_por_dia,
    enviar_correo_cancelacion_admin,
    generar_citas_para_local,
    marcar_citas_atendidas,
)


def make_local(hora_apertura, hora_cierre, num_mecanicos, nombre="TestLocal"):
    municipio = Municipio.objects.create(nombre="TestMunicipio", departamento="TestDepto")
    sede = Sede.objects.create(nombre="TestSede", direccion="Calle 1", municipio=municipio)
    # Convertir hora_apertura/hora_cierre a la nueva estructura horarios
    # Se asignan todos los días para que los tests funcionen igual que antes
    horarios = [
        {
            "dias": ["lun", "mar", "mie", "jue", "vie", "sab", "dom"],
            "apertura": hora_apertura.strftime("%H:%M"),
            "cierre": hora_cierre.strftime("%H:%M"),
        }
    ]
    return Local.objects.create(
        nombre=nombre,
        sede=sede,
        direccion="Calle 2",
        telefono="3001234567",
        correo_admin="admin@test.com",
        num_mecanicos=num_mecanicos,
        horarios=horarios,
    )


# ─────────────────────────────────────────
# citas_por_dia
# ─────────────────────────────────────────


class CitasPorDiaTest(TestCase):
    def test_caso_base(self):
        """6am-6pm, 3 mecánicos → 5 slots (saltando almuerzo) × 3 = 15"""
        local = make_local(time(6, 0), time(18, 0), 3)
        self.assertEqual(citas_por_dia(local), 15)

    def test_horario_corto(self):
        """8am-12pm, 1 mecánico → 2 slots × 1 = 2"""
        local = make_local(time(8, 0), time(12, 0), 1)
        self.assertEqual(citas_por_dia(local), 2)

    def test_un_solo_slot(self):
        """8am-10am, 2 mecánicos → 1 slot × 2 = 2"""
        local = make_local(time(8, 0), time(10, 0), 2)
        self.assertEqual(citas_por_dia(local), 2)

    def test_muchos_mecanicos(self):
        """6am-6pm, 10 mecánicos → 5 slots × 10 = 50"""
        local = make_local(time(6, 0), time(18, 0), 10)
        self.assertEqual(citas_por_dia(local), 50)

    def test_hora_sobrante_se_ignora(self):
        """6am-7pm → 6 slots completos × 3 mec = 18"""
        local = make_local(time(6, 0), time(19, 0), 3)
        self.assertEqual(citas_por_dia(local), 18)  # antes 15 → ahora 18

    def test_un_mecanico_dia_completo(self):
        """6am-6pm, 1 mecánico → 5 slots × 1 = 5"""
        local = make_local(time(6, 0), time(18, 0), 1)
        self.assertEqual(citas_por_dia(local), 5)

    def test_dos_mecanicos(self):
        """8am-4pm, 2 mecánicos → 3 slots (8-10,10-12,13-15) × 2 = 6"""
        local = make_local(time(8, 0), time(16, 0), 2)
        self.assertEqual(citas_por_dia(local), 6)

    def test_horario_tarde(self):
        """12pm-8pm, 1 mecánico → 3 slots (13-15,15-17,17-19... 12-14 salta) → 13-15,15-17,17-19 × 1 = 3"""
        local = make_local(time(12, 0), time(20, 0), 1)
        self.assertEqual(citas_por_dia(local), 3)

    def test_exactamente_dos_horas(self):
        """10am-12pm, 5 mecánicos → 1 slot × 5 = 5"""
        local = make_local(time(10, 0), time(12, 0), 5)
        self.assertEqual(citas_por_dia(local), 5)

    def test_horario_con_minutos_sobrantes(self):
        """8am-11:30am → 1 slot (8-10) × 2 mec = 2"""
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
        """6am-6pm, 3 mecánicos → 5 slots × 3 = 15 citas en DB"""
        local = make_local(time(6, 0), time(18, 0), 3)
        citas = generar_citas_para_local(local, date(2025, 1, 15))
        self.assertEqual(len(citas), 15)  # 5 slots × 3 mec = 15

    def test_almuerzo_bloquea_slot(self):
        """Slot 12-14 no debe generarse (almuerzo 12-13)"""
        local = make_local(time(6, 0), time(18, 0), 1)
        generar_citas_para_local(local, date(2025, 1, 15))
        # No debe existir cita que empiece a las 12:00
        self.assertFalse(Cita.objects.filter(hora_inicio=time(12, 0)).exists())

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


# ─────────────────────────────────────────
# HU-01 · Agendar servicio técnico
# ─────────────────────────────────────────


class AgendarCitaAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.local = make_local(time(8, 0), time(12, 0), 2)
        self.fecha = date(2026, 4, 20)

    def _cita_libre(self):
        return Cita.objects.create(
            local=self.local,
            fecha=self.fecha,
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
            estado=Cita.Estado.LIBRE,
        )

    def _payload_valido(self):
        return {
            "tipo_servicio": "MANTENIMIENTO",
            "tipo_documento": "CC",
            "cliente_nombre": "Juan Pérez",
            "cliente_documento": "1023456789",
            "cliente_telefono": "3001234567",
            "cliente_correo": "juan@test.com",
            "placa_moto": "ABC12C",
            "referencia_moto": "FZ 150",
            "anio_moto": 2022,
        }

    def test_cp_hu01_01_agendamiento_completo_datos_validos(self):
        """CP-HU01-01 · Caja negra — flujo feliz · CA-01 · CA-03"""
        cita = self._cita_libre()
        response = self.client.patch(
            f"/api/scheduling/agendar/{cita.id}/",
            self._payload_valido(),
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        cita.refresh_from_db()
        self.assertEqual(cita.estado, Cita.Estado.ASIGNADA)
        self.assertIn("cita_id", response.data)

    def test_cp_hu01_02_campo_nombre_vacio_retorna_error(self):
        """CP-HU01-02 · Caja negra — validación · CA-01"""
        cita = self._cita_libre()
        payload = self._payload_valido()
        payload["cliente_nombre"] = ""
        response = self.client.patch(
            f"/api/scheduling/agendar/{cita.id}/",
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        cita.refresh_from_db()
        self.assertEqual(cita.estado, Cita.Estado.LIBRE)

    def test_cp_hu01_03_solo_se_muestran_horarios_disponibles(self):
        """CP-HU01-03 · Caja negra — restricción de negocio · CA-02"""
        Cita.objects.create(
            local=self.local,
            fecha=self.fecha,
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
            estado=Cita.Estado.LIBRE,
        )
        Cita.objects.create(
            local=self.local,
            fecha=self.fecha,
            hora_inicio=time(10, 0),
            hora_fin=time(12, 0),
            estado=Cita.Estado.ASIGNADA,
            cliente_nombre="Cliente previo",
            cliente_documento="000",
            cliente_correo="previo@test.com",
        )
        response = self.client.get(f"/api/scheduling/disponibles/?local={self.local.id}&fecha={self.fecha}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["hora_inicio"], "08:00:00")

    def test_cp_hu01_04_cita_persistida_correctamente_en_bd(self):
        """CP-HU01-04 · Integración · CA-01 · CA-03"""
        cita = self._cita_libre()
        self.client.patch(
            f"/api/scheduling/agendar/{cita.id}/",
            self._payload_valido(),
            format="json",
        )
        cita.refresh_from_db()
        self.assertEqual(cita.estado, Cita.Estado.ASIGNADA)
        self.assertEqual(cita.cliente_nombre, "Juan Pérez")
        self.assertEqual(cita.cliente_documento, "1023456789")
        self.assertEqual(cita.cliente_telefono, "3001234567")
        self.assertEqual(cita.cliente_correo, "juan@test.com")
        self.assertEqual(cita.placa_moto, "ABC12C")
        self.assertEqual(cita.referencia_moto, "FZ 150")
        self.assertEqual(cita.anio_moto, 2022)
        self.assertEqual(cita.tipo_servicio, "MANTENIMIENTO")
        self.assertEqual(cita.tipo_documento, "CC")


# ─────────────────────────────────────────
# HU-03 · Recibir confirmación del servicio técnico
# ─────────────────────────────────────────


class ConfirmacionCorreoTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.local = make_local(time(8, 0), time(12, 0), 2)
        self.fecha = date(2026, 4, 20)

    def _cita_libre(self):
        return Cita.objects.create(
            local=self.local,
            fecha=self.fecha,
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
            estado=Cita.Estado.LIBRE,
        )

    def _payload_valido(self):
        return {
            "tipo_servicio": "MANTENIMIENTO",
            "tipo_documento": "CC",
            "cliente_nombre": "Juan Pérez",
            "cliente_documento": "1023456789",
            "cliente_telefono": "3001234567",
            "cliente_correo": "juan@test.com",
            "placa_moto": "ABC12C",
            "referencia_moto": "FZ 150",
            "anio_moto": 2022,
        }

    def test_cp_hu03_01_correo_enviado_automaticamente_tras_agendamiento(self):
        """CP-HU03-01 · Caja negra — flujo feliz · CA-01"""
        cita = self._cita_libre()
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            from django.core import mail

            self.client.patch(
                f"/api/scheduling/agendar/{cita.id}/",
                self._payload_valido(),
                format="json",
            )
            self.assertEqual(len(mail.outbox), 1)
            correo = mail.outbox[0]
            self.assertIn("Juan Pérez", correo.body)
            self.assertIn("20/04/2026", correo.body)
            self.assertIn("08:00", correo.body)
            self.assertIn("Mantenimiento General", correo.body)
            self.assertEqual(correo.to, ["juan@test.com"])

    def test_cp_hu03_02_correo_no_se_envia_si_agendamiento_falla(self):
        """CP-HU03-02 · Caja negra — validación · CA-01"""
        cita = self._cita_libre()
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            from django.core import mail

            payload = self._payload_valido()
            payload["cliente_nombre"] = ""
            self.client.patch(
                f"/api/scheduling/agendar/{cita.id}/",
                payload,
                format="json",
            )
            self.assertEqual(len(mail.outbox), 0)

    def test_cp_hu03_03_estado_envio_queda_registrado(self):
        """CP-HU03-03 · Integración · CA-02"""
        cita = self._cita_libre()
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            self.client.patch(
                f"/api/scheduling/agendar/{cita.id}/",
                self._payload_valido(),
                format="json",
            )
            cita.refresh_from_db()
            self.assertTrue(cita.correo_confirmacion_enviado)
            self.assertIsNotNone(cita.fecha_envio_confirmacion)
            self.assertEqual(cita.error_envio_confirmacion, "")


# ─────────────────────────────────────────
# HU-06 · Recibir notificación de cancelación
# ─────────────────────────────────────────


class NotificacionCancelacionTest(TestCase):
    def setUp(self):
        self.local = make_local(time(8, 0), time(12, 0), 2, nombre="Local Rallye Motor's - Carepa")
        self.fecha = date(2026, 4, 21)

    def _cita_cancelada(self):
        return Cita.objects.create(
            local=self.local,
            fecha=self.fecha,
            hora_inicio=time(16, 0),
            hora_fin=time(18, 0),
            estado=Cita.Estado.CANCELADA,
            tipo_servicio=Cita.TipoServicio.MANTENIMIENTO,
            tipo_documento=Cita.TipoDocumento.CC,
            cliente_nombre="Juan Pérez",
            cliente_documento="1023456789",
            cliente_telefono="3001234567",
            cliente_correo="juan@test.com",
            placa_moto="ABC12C",
            referencia_moto="FZ 150",
            anio_moto=2022,
        )

    def _cita_asignada(self):
        return Cita.objects.create(
            local=self.local,
            fecha=self.fecha,
            hora_inicio=time(16, 0),
            hora_fin=time(18, 0),
            estado=Cita.Estado.ASIGNADA,
            tipo_servicio=Cita.TipoServicio.MANTENIMIENTO,
            tipo_documento=Cita.TipoDocumento.CC,
            cliente_nombre="Juan Pérez",
            cliente_documento="1023456789",
            cliente_telefono="3001234567",
            cliente_correo="juan@test.com",
            placa_moto="ABC12C",
            referencia_moto="FZ 150",
            anio_moto=2022,
        )

    def test_cp_hu06_01_notificacion_enviada_al_admin_tras_cancelacion(self):
        """CP-HU06-01 · Caja negra — flujo feliz · CA-01 · CA-02"""
        cita = self._cita_cancelada()
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            from django.core import mail

            resultado = enviar_correo_cancelacion_admin(cita)

            self.assertTrue(resultado)
            self.assertEqual(len(mail.outbox), 1)

            correo = mail.outbox[0]
            self.assertIn("21/04/2026", correo.body)
            self.assertIn("04:00 PM", correo.body)
            self.assertIn("06:00 PM", correo.body)
            self.assertIn("Mantenimiento General", correo.body)

    def test_cp_hu06_02_notificacion_llega_solo_al_admin_del_local_correcto(self):
        """CP-HU06-02 · Caja negra — restricción de negocio · CA-02"""
        cita = self._cita_cancelada()
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            from django.core import mail

            enviar_correo_cancelacion_admin(cita)

            self.assertEqual(len(mail.outbox), 1)
            correo = mail.outbox[0]
            self.assertEqual(correo.to, [cita.local.correo_admin])

    def test_cp_hu06_03_no_se_envia_si_no_hay_evento_de_cancelacion(self):
        """CP-HU06-03 · Caja negra — validación · CA-01"""
        cita = self._cita_asignada()
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            from django.core import mail

            resultado = enviar_correo_cancelacion_admin(cita)

            self.assertFalse(resultado)
            self.assertEqual(len(mail.outbox), 0)
            cita.refresh_from_db()
            self.assertFalse(cita.correo_cancelacion_enviado)
            self.assertIsNone(cita.fecha_envio_cancelacion)
            self.assertEqual(cita.error_envio_cancelacion, "")


# ─────────────────────────────────────────
# Marcar citas atendidas (lazy update)
# ─────────────────────────────────────────


class MarcarCitasAtendidasTest(TestCase):
    def setUp(self):
        self.local = make_local(time(6, 0), time(18, 0), 1)

    def _cita_asignada(self, fecha, hora_inicio, hora_fin):
        return Cita.objects.create(
            local=self.local,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            estado=Cita.Estado.ASIGNADA,
            tipo_servicio=Cita.TipoServicio.MANTENIMIENTO,
            tipo_documento=Cita.TipoDocumento.CC,
            cliente_nombre="Juan Pérez",
            cliente_documento="1023456789",
            cliente_telefono="3001234567",
            cliente_correo="juan@test.com",
            placa_moto="ABC12C",
            referencia_moto="FZ 150",
            anio_moto=2022,
        )

    def test_cita_de_fecha_pasada_queda_atendida(self):
        """Cita ASIGNADA con fecha anterior a hoy → pasa a ATENDIDO."""
        cita = self._cita_asignada(date(2025, 1, 1), time(8, 0), time(10, 0))
        total = marcar_citas_atendidas()
        cita.refresh_from_db()
        self.assertEqual(cita.estado, Cita.Estado.ATENDIDO)
        self.assertEqual(total, 1)

    def test_cita_futura_no_se_toca(self):
        """Cita ASIGNADA con fecha futura → permanece ASIGNADA."""
        cita = self._cita_asignada(date(2030, 1, 1), time(8, 0), time(10, 0))
        marcar_citas_atendidas()
        cita.refresh_from_db()
        self.assertEqual(cita.estado, Cita.Estado.ASIGNADA)

    def test_cita_libre_no_se_toca(self):
        """Cita LIBRE con fecha pasada → permanece LIBRE, no se marca ATENDIDO."""
        cita = Cita.objects.create(
            local=self.local,
            fecha=date(2025, 1, 1),
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
            estado=Cita.Estado.LIBRE,
        )
        marcar_citas_atendidas()
        cita.refresh_from_db()
        self.assertEqual(cita.estado, Cita.Estado.LIBRE)

    def test_multiples_citas_vencidas_todas_se_marcan(self):
        """Varias citas ASIGNADAS con fecha pasada → todas pasan a ATENDIDO."""
        self._cita_asignada(date(2025, 1, 1), time(8, 0), time(10, 0))
        self._cita_asignada(date(2025, 1, 2), time(10, 0), time(12, 0))
        self._cita_asignada(date(2025, 1, 3), time(14, 0), time(16, 0))
        total = marcar_citas_atendidas()
        self.assertEqual(total, 3)
        self.assertEqual(Cita.objects.filter(estado=Cita.Estado.ATENDIDO).count(), 3)

    def test_retorna_cero_si_no_hay_citas_vencidas(self):
        """Sin citas vencidas → retorna 0."""
        self._cita_asignada(date(2030, 1, 1), time(8, 0), time(10, 0))
        total = marcar_citas_atendidas()
        self.assertEqual(total, 0)



# ─────────────────────────────────────────
# HU-19 · Visualizar agenda de atención
# ─────────────────────────────────────────


class AgendaAdminTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.local = make_local(time(8, 0), time(18, 0), 2)
        self.fecha = date(2026, 5, 10)

        # Crear usuario admin vinculado al local
        from users.models import User
        self.user = User.objects.create_user(
            username="admin_test",
            password="testpass123",
            local=self.local,
        )
        self.client.force_authenticate(user=self.user)

    def _cita(self, estado, hora_inicio=time(8, 0), hora_fin=time(10, 0), **kwargs):
        defaults = dict(
            local=self.local,
            fecha=self.fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            estado=estado,
            tipo_servicio=Cita.TipoServicio.MANTENIMIENTO,
            tipo_documento=Cita.TipoDocumento.CC,
            cliente_nombre="Laura Torres",
            cliente_documento="1099887766",
            cliente_telefono="3109876543",
            cliente_correo="laura@test.com",
            placa_moto="XYZ45W",
            referencia_moto="MT-03",
            anio_moto=2023,
        )
        defaults.update(kwargs)
        return Cita.objects.create(**defaults)

    def test_cp_hu19_01_agenda_retorna_solo_citas_no_libres(self):
        """CP-HU19-01 · Caja negra — flujo feliz · CA-01
        La agenda no debe mostrar citas LIBRE, solo ASIGNADA y ATENDIDO."""
        self._cita(Cita.Estado.LIBRE)
        self._cita(Cita.Estado.ASIGNADA, hora_inicio=time(10, 0), hora_fin=time(12, 0))
        self._cita(Cita.Estado.ATENDIDO, hora_inicio=time(13, 0), hora_fin=time(15, 0))

        response = self.client.get(f"/api/scheduling/agenda/?fecha={self.fecha}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        estados = {c["estado"] for c in response.data}
        self.assertNotIn("LIBRE", estados)

    def test_cp_hu19_02_agenda_ordenada_por_hora_inicio(self):
        """CP-HU19-02 · Caja negra — CA-01
        Las citas deben venir ordenadas de menor a mayor hora."""
        self._cita(Cita.Estado.ASIGNADA, hora_inicio=time(13, 0), hora_fin=time(15, 0))
        self._cita(Cita.Estado.ASIGNADA, hora_inicio=time(8, 0), hora_fin=time(10, 0))
        self._cita(Cita.Estado.ATENDIDO, hora_inicio=time(10, 0), hora_fin=time(12, 0))

        response = self.client.get(f"/api/scheduling/agenda/?fecha={self.fecha}")

        self.assertEqual(response.status_code, 200)
        horas = [c["hora_inicio"] for c in response.data]
        self.assertEqual(horas, sorted(horas))

    def test_cp_hu19_03_sin_fecha_retorna_400(self):
        """CP-HU19-03 · Caja negra — validación · CA-01
        Sin el parámetro fecha el endpoint debe retornar 400."""
        response = self.client.get("/api/scheduling/agenda/")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_cp_hu19_04_fecha_invalida_retorna_400(self):
        """CP-HU19-04 · Caja negra — validación · CA-01
        Una fecha con formato incorrecto debe retornar 400."""
        response = self.client.get("/api/scheduling/agenda/?fecha=32-13-2026")
        self.assertEqual(response.status_code, 400)

    def test_cp_hu19_05_sin_autenticacion_retorna_401(self):
        """CP-HU19-05 · Seguridad · CA-01
        Un cliente sin token no debe poder acceder a la agenda."""
        client_anonimo = APIClient()
        response = client_anonimo.get(f"/api/scheduling/agenda/?fecha={self.fecha}")
        self.assertEqual(response.status_code, 401)

    def test_cp_hu19_06_admin_sin_local_retorna_403(self):
        """CP-HU19-06 · Seguridad · CA-01
        Un admin sin local asignado debe recibir 403."""
        from users.models import User
        user_sin_local = User.objects.create_user(
            username="admin_sin_local",
            email="sin_local@test.com",
            password="testpass123",
            local=None,
        )
        client2 = APIClient()
        client2.force_authenticate(user=user_sin_local)
        response = client2.get(f"/api/scheduling/agenda/?fecha={self.fecha}")
        self.assertEqual(response.status_code, 403)

    def test_cp_hu19_07_admin_solo_ve_citas_de_su_local(self):
        """CP-HU19-07 · Restricción de negocio · CA-01
        El admin no debe ver citas de otro local."""
        otro_local = make_local(time(8, 0), time(18, 0), 1, nombre="OtroLocal")
        Cita.objects.create(
            local=otro_local,
            fecha=self.fecha,
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
            estado=Cita.Estado.ASIGNADA,
            tipo_servicio=Cita.TipoServicio.MANTENIMIENTO,
            tipo_documento=Cita.TipoDocumento.CC,
            cliente_nombre="Otro Cliente",
            cliente_documento="000",
            cliente_telefono="3000000000",
            cliente_correo="otro@test.com",
            placa_moto="ZZZ99Z",
            referencia_moto="NMAX",
            anio_moto=2021,
        )
        self._cita(Cita.Estado.ASIGNADA, hora_inicio=time(10, 0), hora_fin=time(12, 0))

        response = self.client.get(f"/api/scheduling/agenda/?fecha={self.fecha}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["local_nombre"], self.local.nombre)

    def test_cp_hu19_08_dia_sin_citas_retorna_lista_vacia(self):
        """CP-HU19-08 · Caja negra — CA-01
        Un día sin citas asignadas ni atendidas retorna lista vacía."""
        response = self.client.get("/api/scheduling/agenda/?fecha=2099-01-01")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_cp_hu19_09_campos_obligatorios_presentes_en_respuesta(self):
        """CP-HU19-09 · Integración · CA-01
        La respuesta debe incluir todos los campos requeridos por la HU."""
        self._cita(Cita.Estado.ASIGNADA)
        response = self.client.get(f"/api/scheduling/agenda/?fecha={self.fecha}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        cita = response.data[0]

        campos_requeridos = [
            "id", "fecha", "hora_inicio", "hora_fin",
            "estado", "estado_display", "tipo_servicio", "tipo_servicio_display",
            "cliente_nombre", "cliente_documento", "tipo_documento",
            "cliente_telefono", "cliente_correo",
            "placa_moto", "referencia_moto", "anio_moto",
            "local_nombre", "sede_nombre",
        ]
        for campo in campos_requeridos:
            self.assertIn(campo, cita, msg=f"Campo ausente: {campo}")

    def test_cp_hu19_10_canceladas_aparecen_en_agenda(self):
        """CP-HU19-10 · Caja negra — CA-01
        Las citas CANCELADA también deben aparecer en la agenda."""
        self._cita(Cita.Estado.CANCELADA)
        response = self.client.get(f"/api/scheduling/agenda/?fecha={self.fecha}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["estado"], "CANCELADA")
