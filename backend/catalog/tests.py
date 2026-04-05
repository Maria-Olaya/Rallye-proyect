# catalog/tests.py  — agrega estas clases al archivo existente

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


# ── HU-11 · Visualizar catálogo ──────────────────────────────────────────────


class VisualizarCatalogoTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.moto_activa = Motocicleta.objects.create(
            referencia="MT-07",
            anio=2024,
            tipo="DEPORTIVA",
            cilindraje=689,
            precio="28000000.00",
            caracteristicas="Motor bicilíndrico, frenos ABS, pantalla TFT.",
            activa=True,
        )
        self.moto_inactiva = Motocicleta.objects.create(
            referencia="YBR 125",
            anio=2020,
            tipo="URBANA",
            cilindraje=125,
            precio="8000000.00",
            caracteristicas="Moto básica de ciudad.",
            activa=False,
        )

    def test_cp_hu11_01_catalogo_retorna_solo_motos_activas(self):
        """CP-HU11-01 · Unitaria — flujo feliz · CA-01"""
        response = self.client.get("/api/catalog/motocicletas/")
        self.assertEqual(response.status_code, 200)
        referencias = [m["referencia"] for m in response.data]
        self.assertIn("MT-07", referencias)
        self.assertNotIn("YBR 125", referencias)

    def test_cp_hu11_02_catalogo_retorna_campos_requeridos(self):
        """CP-HU11-02 · Unitaria — campos · CA-02"""
        response = self.client.get("/api/catalog/motocicletas/")
        self.assertEqual(response.status_code, 200)
        moto = response.data[0]
        for campo in ["id", "marca", "referencia", "anio", "tipo_display",
                      "cilindraje", "precio_display", "caracteristicas"]:
            self.assertIn(campo, moto)

    def test_cp_hu11_03_catalogo_vacio_retorna_lista_vacia(self):
        """CP-HU11-03 · Unitaria — flujo alternativo · CA-01"""
        Motocicleta.objects.filter(activa=True).update(activa=False)
        response = self.client.get("/api/catalog/motocicletas/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_cp_hu11_04_catalogo_no_requiere_autenticacion(self):
        """CP-HU11-04 · Control de acceso — endpoint público · CA-01"""
        self.client.credentials()
        response = self.client.get("/api/catalog/motocicletas/")
        self.assertEqual(response.status_code, 200)

    def test_cp_hu11_05_integracion_datos_correctos_desde_bd(self):
        """CP-HU11-05 · Integración · CA-03"""
        response = self.client.get("/api/catalog/motocicletas/")
        moto = next(m for m in response.data if m["referencia"] == "MT-07")
        self.assertEqual(moto["anio"], 2024)
        self.assertEqual(moto["cilindraje"], 689)
        self.assertEqual(moto["marca"], "Yamaha")
        self.assertEqual(moto["tipo_display"], "Deportiva")

    def test_cp_hu11_06_multiples_motos_activas_todas_aparecen(self):
        """CP-HU11-06 · Unitaria — flujo feliz · CA-01
        Con varias motos activas, el catálogo las retorna todas.
        Resultado esperado: HTTP 200 · lista con todas las motos activas."""
        Motocicleta.objects.create(
            referencia="NMAX 155",
            anio=2023,
            tipo="AUTOMATICA",
            cilindraje=155,
            precio="12000000.00",
            caracteristicas="Scooter automático con frenos ABS.",
            activa=True,
        )
        response = self.client.get("/api/catalog/motocicletas/")
        self.assertEqual(response.status_code, 200)
        referencias = [m["referencia"] for m in response.data]
        self.assertIn("MT-07", referencias)
        self.assertIn("NMAX 155", referencias)
        self.assertEqual(len(referencias), 2)


    def test_cp_hu11_07_motos_de_diferentes_tipos_coexisten_en_catalogo(self):
        """CP-HU11-07 · Unitaria — flujo alternativo · CA-02
        Motos activas de distintos tipos aparecen todas en el catálogo.
        Resultado esperado: HTTP 200 · cada tipo está representado en la respuesta."""
        Motocicleta.objects.create(
            referencia="XTZ 125",
            anio=2022,
            tipo="TODOTERRENO",
            cilindraje=125,
            precio="11000000.00",
            caracteristicas="Moto todoterreno ligera.",
            activa=True,
        )
        response = self.client.get("/api/catalog/motocicletas/")
        self.assertEqual(response.status_code, 200)
        tipos = [m["tipo_display"] for m in response.data]
        self.assertIn("Deportiva", tipos)
        self.assertIn("Todoterreno", tipos)
        self.assertNotIn("Urbana", tipos)  # la moto urbana está inactiva   
