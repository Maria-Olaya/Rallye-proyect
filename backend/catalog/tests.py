# catalog/tests.py

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from catalog.models import Motocicleta
from core.models import Local, Municipio, Sede

User = get_user_model()


# ── Helpers ───────────────────────────────────────────────────────────────────


def make_local():
    municipio = Municipio.objects.create(nombre="TestMunicipio", departamento="TestDepto")
    sede = Sede.objects.create(nombre="TestSede", direccion="Calle 1", municipio=municipio)
    return Local.objects.create(
        nombre="Local Test",
        sede=sede,
        direccion="Calle 2",
        telefono="3001234567",
        correo_admin="admin@test.com",
        hora_apertura="08:00",
        hora_cierre="18:00",
        num_mecanicos=2,
    )


def make_admin(local):
    return User.objects.create_user(
        username="admintest",
        email="admin@rallye.com",
        password="Segura123!",
        local=local,
    )


def get_token(user):
    return str(RefreshToken.for_user(user).access_token)


# ── HU-13 · Agregar motocicleta ───────────────────────────────────────────────


class AgregarMotocicletaTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.local = make_local()
        self.admin = make_admin(self.local)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(self.admin)}")

    def _payload_valido(self):
        return {
            "referencia": "FZ 150",
            "anio": 2024,
            "tipo": "URBANA",
            "cilindraje": 150,
            "precio": "9500000.00",
            "caracteristicas": "Moto urbana de bajo cilindraje ideal para ciudad.",
        }

    def test_cp_hu13_01_admin_agrega_moto_correctamente(self):
        """CP-HU13-01 · Caja negra — flujo feliz · CA-01 · CA-02 · CA-03"""
        response = self.client.post(
            "/api/catalog/motocicletas/agregar/",
            self._payload_valido(),
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Motocicleta.objects.filter(referencia="FZ 150").exists())
        moto = Motocicleta.objects.get(referencia="FZ 150")
        self.assertTrue(moto.activa)
        self.assertEqual(moto.marca, "Yamaha")

    def test_cp_hu13_02_sin_autenticacion_retorna_401(self):
        """CP-HU13-02 · Control de acceso · CA-01"""
        self.client.credentials()
        response = self.client.post(
            "/api/catalog/motocicletas/agregar/",
            self._payload_valido(),
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertFalse(Motocicleta.objects.filter(referencia="FZ 150").exists())

    def test_cp_hu13_03_campo_obligatorio_vacio_retorna_400(self):
        """CP-HU13-03 · Caja negra — validación · CA-01"""
        payload = self._payload_valido()
        payload["referencia"] = ""
        response = self.client.post(
            "/api/catalog/motocicletas/agregar/",
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Motocicleta.objects.exists())

    def test_cp_hu13_04_moto_creada_queda_en_bd_con_datos_correctos(self):
        """CP-HU13-04 · Integración · CA-03"""
        self.client.post(
            "/api/catalog/motocicletas/agregar/",
            self._payload_valido(),
            format="json",
        )
        moto = Motocicleta.objects.get(referencia="FZ 150")
        self.assertEqual(moto.marca, "Yamaha")
        self.assertEqual(moto.cilindraje, 150)
        self.assertEqual(moto.anio, 2024)
        self.assertEqual(moto.tipo, "URBANA")
        self.assertTrue(moto.activa)

    def test_cp_hu13_05_cilindraje_cero_retorna_400(self):
        """CP-HU13-05 · Caja negra — validación · CA-01"""
        payload = self._payload_valido()
        payload["cilindraje"] = 0
        response = self.client.post(
            "/api/catalog/motocicletas/agregar/",
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Motocicleta.objects.exists())

    def test_cp_hu13_06_anio_invalido_retorna_400(self):
        """CP-HU13-06 · Caja negra — validación · CA-01"""
        payload = self._payload_valido()
        payload["anio"] = 1800
        response = self.client.post(
            "/api/catalog/motocicletas/agregar/",
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Motocicleta.objects.exists())

    def test_cp_hu13_07_precio_negativo_retorna_400(self):
        """CP-HU13-07 · Caja negra — validación · CA-01"""
        payload = self._payload_valido()
        payload["precio"] = "-1000.00"
        response = self.client.post(
            "/api/catalog/motocicletas/agregar/",
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Motocicleta.objects.exists())
