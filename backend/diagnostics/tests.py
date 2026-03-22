from datetime import date, time

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Local, Municipio, Sede
from diagnostics.models import Diagnostico
from scheduling.models import Cita


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

    def _crear_cita(self, estado, placa="ABC123"):
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
        self._crear_cita(Cita.Estado.ASIGNADA, placa="ZZZ999")
        cita = self._crear_cita(Cita.Estado.ATENDIDO)

        response = self.client.get("/api/diagnostics/buscar-cita/?placa=ABC123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], cita.id)
        self.assertEqual(response.data["placa_moto"], "ABC123")

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

        response = self.client.post(
            "/api/diagnostics/",
            {"cita_id": cita.id, "descripcion": "Se realizó ajuste de frenos y cambio de aceite."},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        diagnostico = Diagnostico.objects.get(cita=cita)
        self.assertEqual(diagnostico.registrado_por, self.user)
        self.assertTrue(diagnostico.radicado.startswith("RAD-"))
        self.assertFalse(diagnostico.correo_radicado_enviado)
