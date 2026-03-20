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
)


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


# ─────────────────────────────────────────
# HU-01 · Agendar servicio técnico
# ─────────────────────────────────────────


class AgendarCitaAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.local = make_local(time(8, 0), time(12, 0), 2)
        self.fecha = date(2026, 4, 20)

    def _cita_libre(self):
        """Crea y retorna una cita en estado LIBRE para usar en los tests."""
        return Cita.objects.create(
            local=self.local,
            fecha=self.fecha,
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
            estado=Cita.Estado.LIBRE,
        )

    def _payload_valido(self):
        """Payload completo con todos los datos válidos para agendar."""
        return {
            "tipo_servicio": "MANTENIMIENTO",
            "tipo_documento": "CC",
            "cliente_nombre": "Juan Pérez",
            "cliente_documento": "1023456789",
            "cliente_telefono": "3001234567",
            "cliente_correo": "juan@test.com",
            "placa_moto": "ABC123",
            "referencia_moto": "FZ 150",
            "anio_moto": 2022,
        }

    def test_cp_hu01_01_agendamiento_completo_datos_validos(self):
        """CP-HU01-01 · Caja negra — flujo feliz · CA-01 · CA-03
        Agendamiento completo con todos los datos válidos.
        Resultado esperado: cita registrada en BD · estado cambia a ASIGNADA · HTTP 200."""
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
        """CP-HU01-02 · Caja negra — validación · CA-01
        Campo obligatorio vacío (nombre).
        Resultado esperado: HTTP 400 · cita permanece en estado LIBRE."""
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
        """CP-HU01-03 · Caja negra — restricción de negocio · CA-02
        Local con slots parcialmente ocupados.
        Resultado esperado: endpoint retorna solo citas en estado LIBRE."""
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
        """CP-HU01-04 · Integración · CA-01 · CA-03
        Cita queda persistida en BD con todos los campos correctos.
        Resultado esperado: registro visible en BD con datos del cliente y moto."""
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
        self.assertEqual(cita.placa_moto, "ABC123")
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
        """Crea y retorna una cita en estado LIBRE para usar en los tests."""
        return Cita.objects.create(
            local=self.local,
            fecha=self.fecha,
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
            estado=Cita.Estado.LIBRE,
        )

    def _payload_valido(self):
        """Payload completo con todos los datos válidos para agendar."""
        return {
            "tipo_servicio": "MANTENIMIENTO",
            "tipo_documento": "CC",
            "cliente_nombre": "Juan Pérez",
            "cliente_documento": "1023456789",
            "cliente_telefono": "3001234567",
            "cliente_correo": "juan@test.com",
            "placa_moto": "ABC123",
            "referencia_moto": "FZ 150",
            "anio_moto": 2022,
        }

    def test_cp_hu03_01_correo_enviado_automaticamente_tras_agendamiento(self):
        """CP-HU03-01 · Caja negra — flujo feliz · CA-01
        Correo enviado automáticamente tras agendamiento válido.
        Resultado esperado: correo enviado con fecha, hora, sede y categoría correctas."""
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
        """CP-HU03-02 · Caja negra — validación · CA-01
        Correo no se envía si los datos del agendamiento son inválidos.
        Resultado esperado: no se envía correo · error mostrado al usuario."""
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
        """CP-HU03-03 · Integración · CA-02
        El estado de envío del correo queda registrado correctamente en BD.
        Resultado esperado: correo_confirmacion_enviado = True tras agendamiento exitoso."""
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
        """Crea y retorna una cita cancelada con datos completos para usar en los tests."""
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
            placa_moto="ABC123",
            referencia_moto="FZ 150",
            anio_moto=2022,
        )

    def _cita_asignada(self):
        """Crea y retorna una cita asignada para probar el caso donde no hay cancelación."""
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
            placa_moto="ABC123",
            referencia_moto="FZ 150",
            anio_moto=2022,
        )

    def test_cp_hu06_01_notificacion_enviada_al_admin_tras_cancelacion(self):
        """CP-HU06-01 · Caja negra — flujo feliz · CA-01 · CA-02
        Notificación enviada al admin tras cancelación.
        Resultado esperado: correo enviado con fecha, hora y categoría del servicio cancelado."""
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
        """CP-HU06-02 · Caja negra — restricción de negocio · CA-02
        Notificación llega solo al admin del local correcto.
        Resultado esperado: el destinatario es únicamente correo_admin del local asociado."""
        cita = self._cita_cancelada()
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            from django.core import mail

            enviar_correo_cancelacion_admin(cita)

            self.assertEqual(len(mail.outbox), 1)
            correo = mail.outbox[0]
            self.assertEqual(correo.to, [cita.local.correo_admin])

    def test_cp_hu06_03_no_se_envia_si_no_hay_evento_de_cancelacion(self):
        """CP-HU06-03 · Caja negra — validación · CA-01
        No se envía si no hay evento de cancelación.
        Resultado esperado: función retorna False y no se genera correo."""
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
