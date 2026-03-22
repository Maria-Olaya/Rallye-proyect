from datetime import date, time

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Local, Municipio, Sede
from diagnostics.models import Diagnostico
from diagnostics.services import enviar_radicado_por_correo
from scheduling.models import Cita


# ── Helper compartido ─────────────────────────────────────────────────────────


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


# ── HU-04 · Registrar diagnóstico ─────────────────────────────────────────────


class DiagnosticoApiTests(TestCase):
    def setUp(self):
        municipio = Municipio.objects.create(nombre="Medellin", departamento="Antioquia")
        sede = Sede.objects.create(nombre="Centro", municipio=municipio, direccion="Cra 1")
        self.local = Local.objects.create(
            nombre="Local Centro",
            sede=sede,
            direccion="Cra 1 # 1-1",
            telefono="3000000000",
            correo_admin="admin@local.com",
            activo=True,
            hora_apertura=time(8, 0),
            hora_cierre=time(18, 0),
            num_mecanicos=2,
        )
        self.user = get_user_model().objects.create_user(
            username="adminlocal",
            email="admin@rallye.com",
            password="Segura123!",
            local=self.local,
        )
        self.client = APIClient()
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _crear_cita(self, estado, placa="ABC12C"):
        return Cita.objects.create(
            local=self.local,
            fecha=date(2026, 3, 21),
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
            estado=estado,
            tipo_servicio=Cita.TipoServicio.MANTENIMIENTO,
            tipo_documento=Cita.TipoDocumento.CC,
            cliente_nombre="Juan Perez",
            cliente_documento="10203040",
            cliente_telefono="3001234567",
            cliente_correo="juan@test.com",
            placa_moto=placa,
            referencia_moto="FZ 150",
            anio_moto=2022,
        )

    def test_busqueda_por_placa_solo_retorna_cita_atendida(self):
        self._crear_cita(Cita.Estado.ASIGNADA, placa="ZZZ99Z")
        cita = self._crear_cita(Cita.Estado.ATENDIDO)

        response = self.client.get("/api/diagnostics/buscar-cita/?placa=ABC12C")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], cita.id)
        self.assertEqual(response.data["placa_moto"], "ABC12C")

    def test_no_permite_diagnostico_si_cita_no_esta_atendida(self):
        cita = self._crear_cita(Cita.Estado.ASIGNADA)

        response = self.client.post(
            "/api/diagnostics/",
            {"cita_id": cita.id, "descripcion": "Se reviso y se cambiaron piezas."},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("ATENDIDO", response.data["cita_id"][0])

    def test_crea_diagnostico_y_radicado_unico(self):
        cita = self._crear_cita(Cita.Estado.ATENDIDO)

        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            response = self.client.post(
                "/api/diagnostics/",
                {"cita_id": cita.id, "descripcion": "Se realizó ajuste de frenos y cambio de aceite."},
                format="json",
            )

        self.assertEqual(response.status_code, 201)
        diagnostico = Diagnostico.objects.get(cita=cita)
        self.assertEqual(diagnostico.registrado_por, self.user)
        self.assertTrue(diagnostico.radicado.startswith("RAD-"))
        self.assertTrue(diagnostico.correo_radicado_enviado)


# ── HU-05 · Enviar radicado por correo ───────────────────────────────────────


class EnviarRadicadoCorreoTest(TestCase):
    def setUp(self):
        self.local = make_local(time(8, 0), time(12, 0), 2, nombre="Local Rallye Motor's - Carepa")
        self.fecha = date(2026, 4, 21)

    def _cita_con_correo(self):
        return Cita.objects.create(
            local=self.local,
            fecha=self.fecha,
            hora_inicio=time(16, 0),
            hora_fin=time(18, 0),
            estado=Cita.Estado.ASIGNADA,
            tipo_servicio=Cita.TipoServicio.REVISION,
            tipo_documento=Cita.TipoDocumento.CC,
            cliente_nombre="Isabella",
            cliente_documento="1020105102",
            cliente_telefono="3145941558",
            cliente_correo="isabela23pareja@gmail.com",
            placa_moto="ABC12C",
            referencia_moto="FZ 150",
            anio_moto=2022,
        )

    def _cita_sin_correo(self):
        return Cita.objects.create(
            local=self.local,
            fecha=self.fecha,
            hora_inicio=time(8, 0),
            hora_fin=time(10, 0),
            estado=Cita.Estado.LIBRE,
            tipo_servicio=Cita.TipoServicio.REVISION,
            tipo_documento=Cita.TipoDocumento.CC,
            cliente_nombre="Isabella",
            cliente_documento="1020105102",
            cliente_telefono="3145941558",
            cliente_correo="",
            placa_moto="XYZ99Z",
            referencia_moto="FZ 250",
            anio_moto=2021,
        )

    def test_cp_hu05_01_radicado_enviado_automaticamente_tras_diagnostico(self):
        """CP-HU05-01 · Caja negra — flujo feliz · CA-01"""
        cita = self._cita_con_correo()
        diagnostico = Diagnostico.objects.create(
            cita=cita,
            descripcion="Se realizó revisión general de la motocicleta. Se recomienda cambio de pastillas de freno.",
            radicado="RAD-PRUEBA-001",
        )

        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            resultado = enviar_radicado_por_correo(diagnostico)

            self.assertTrue(resultado)
            self.assertEqual(len(mail.outbox), 1)

            correo = mail.outbox[0]
            self.assertIn("RAD-PRUEBA-001", correo.subject)
            self.assertIn("Hola, Isabella,", correo.body)
            self.assertEqual(correo.to, ["isabela23pareja@gmail.com"])
            self.assertEqual(len(correo.attachments), 1)

            adjunto = correo.attachments[0]
            self.assertEqual(adjunto[0], "RAD-PRUEBA-001.pdf")
            self.assertEqual(adjunto[2], "application/pdf")

    def test_cp_hu05_02_no_se_envia_si_correo_cliente_es_invalido_o_vacio(self):
        """CP-HU05-02 · Caja negra — validación · CA-01"""
        cita = self._cita_sin_correo()
        diagnostico = Diagnostico.objects.create(
            cita=cita,
            descripcion="Diagnóstico de prueba sin correo.",
            radicado="RAD-PRUEBA-002",
        )

        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            resultado = enviar_radicado_por_correo(diagnostico)

            self.assertFalse(resultado)
            self.assertEqual(len(mail.outbox), 0)

            diagnostico.refresh_from_db()
            self.assertFalse(diagnostico.correo_radicado_enviado)
            self.assertIsNone(diagnostico.fecha_envio_radicado)

    def test_cp_hu05_03_estado_envio_registrado_en_sistema(self):
        """CP-HU05-03 · Integración · CA-02"""
        cita = self._cita_con_correo()
        diagnostico = Diagnostico.objects.create(
            cita=cita,
            descripcion="Diagnóstico registrado para prueba de integración.",
            radicado="RAD-PRUEBA-003",
        )

        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            resultado = enviar_radicado_por_correo(diagnostico)

            self.assertTrue(resultado)

            diagnostico.refresh_from_db()
            self.assertTrue(diagnostico.correo_radicado_enviado)
            self.assertIsNotNone(diagnostico.fecha_envio_radicado)
