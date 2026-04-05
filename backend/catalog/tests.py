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
        for campo in [
            "id",
            "marca",
            "referencia",
            "anio",
            "tipo_display",
            "cilindraje",
            "precio_display",
            "caracteristicas",
        ]:
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


# ── HU-12 · Filtrar catálogo ─────────────────────────────────────────────────


class FiltrarCatalogoTest(TestCase):
    """
    Cubre los criterios de aceptación de HU-12:
      CA-01  Filtrar por referencia (búsqueda parcial, insensible a mayúsculas).
      CA-02  Filtrar por cilindraje (mín, máx o rango).
      CA-03  Filtrar por tipo de motocicleta.
      CA-04  Resultados se actualizan dinámicamente (combinación de filtros).
    """

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/catalog/motocicletas/"

        # Catálogo base de prueba
        self.fz25 = Motocicleta.objects.create(
            referencia="FZ 25",
            anio=2023,
            tipo="DEPORTIVA",
            cilindraje=250,
            precio="12500000.00",
            caracteristicas="Motor monocilíndrico 250 cc.",
            activa=True,
        )
        self.mt07 = Motocicleta.objects.create(
            referencia="MT-07",
            anio=2024,
            tipo="DEPORTIVA",
            cilindraje=689,
            precio="28000000.00",
            caracteristicas="Motor bicilíndrico 700 cc.",
            activa=True,
        )
        self.xtz125 = Motocicleta.objects.create(
            referencia="XTZ 125",
            anio=2022,
            tipo="TODOTERRENO",
            cilindraje=125,
            precio="9000000.00",
            caracteristicas="Moto todoterreno ligera.",
            activa=True,
        )
        self.nmax = Motocicleta.objects.create(
            referencia="NMAX 155",
            anio=2023,
            tipo="AUTOMATICA",
            cilindraje=155,
            precio="12000000.00",
            caracteristicas="Scooter automático.",
            activa=True,
        )
        # Moto inactiva — nunca debe aparecer en ningún resultado
        self.inactiva = Motocicleta.objects.create(
            referencia="FZ inactiva",
            anio=2021,
            tipo="DEPORTIVA",
            cilindraje=250,
            precio="10000000.00",
            caracteristicas="Fuera de catálogo.",
            activa=False,
        )

    # ── CA-01 · Filtro por referencia ────────────────────────────────────────

    def test_cp_hu12_01_filtro_referencia_retorna_coincidencias(self):
        """CP-HU12-01 · Unitaria — happy path · CA-01
        Buscar 'FZ' debe retornar todas las motos activas cuya referencia
        contenga esa cadena, sin importar mayúsculas.
        Resultado esperado: HTTP 200 · solo la FZ 25 en la lista."""
        response = self.client.get(self.url, {"referencia": "FZ"})
        self.assertEqual(response.status_code, 200)
        referencias = [m["referencia"] for m in response.data]
        self.assertIn("FZ 25", referencias)
        self.assertNotIn("MT-07", referencias)
        self.assertNotIn("XTZ 125", referencias)

    def test_cp_hu12_02_filtro_referencia_insensible_mayusculas(self):
        """CP-HU12-02 · Unitaria — flujo alternativo · CA-01
        La búsqueda 'fz' en minúsculas debe encontrar 'FZ 25' igual que en
        mayúsculas, porque el filtro usa icontains.
        Resultado esperado: HTTP 200 · FZ 25 presente en la respuesta."""
        response = self.client.get(self.url, {"referencia": "fz"})
        self.assertEqual(response.status_code, 200)
        referencias = [m["referencia"] for m in response.data]
        self.assertIn("FZ 25", referencias)

    def test_cp_hu12_03_filtro_referencia_sin_coincidencias_retorna_lista_vacia(self):
        """CP-HU12-03 · Unitaria — flujo alternativo · CA-01
        Una referencia que no existe en el catálogo debe retornar lista vacía,
        no un error.
        Resultado esperado: HTTP 200 · lista vacía []."""
        response = self.client.get(self.url, {"referencia": "INEXISTENTE"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_cp_hu12_04_filtro_referencia_excluye_motos_inactivas(self):
        """CP-HU12-04 · Integración · CA-01
        Aunque 'FZ inactiva' contiene 'FZ', no debe aparecer porque está
        inactiva en el catálogo.
        Resultado esperado: HTTP 200 · 'FZ inactiva' ausente en la respuesta."""
        response = self.client.get(self.url, {"referencia": "FZ"})
        self.assertEqual(response.status_code, 200)
        referencias = [m["referencia"] for m in response.data]
        self.assertNotIn("FZ inactiva", referencias)

    # ── CA-02 · Filtro por cilindraje ────────────────────────────────────────

    def test_cp_hu12_05_filtro_cilindraje_min_retorna_desde_ese_valor(self):
        """CP-HU12-05 · Unitaria — happy path · CA-02
        Con solo cilindraje_min=300 deben aparecer las motos con 300 cc o más;
        las de 125, 155 y 250 cc quedan fuera.
        Resultado esperado: HTTP 200 · solo MT-07 (689 cc)."""
        response = self.client.get(self.url, {"cilindraje_min": 300})
        self.assertEqual(response.status_code, 200)
        referencias = [m["referencia"] for m in response.data]
        self.assertIn("MT-07", referencias)
        self.assertNotIn("FZ 25", referencias)
        self.assertNotIn("XTZ 125", referencias)
        self.assertNotIn("NMAX 155", referencias)

    def test_cp_hu12_06_filtro_cilindraje_max_retorna_hasta_ese_valor(self):
        """CP-HU12-06 · Unitaria — happy path · CA-02
        Con solo cilindraje_max=150 deben aparecer las motos con 150 cc o menos;
        las de 250 cc y 689 cc quedan fuera.
        Resultado esperado: HTTP 200 · solo XTZ 125 (125 cc)."""
        response = self.client.get(self.url, {"cilindraje_max": 150})
        self.assertEqual(response.status_code, 200)
        referencias = [m["referencia"] for m in response.data]
        self.assertIn("XTZ 125", referencias)
        self.assertNotIn("FZ 25", referencias)
        self.assertNotIn("MT-07", referencias)
        self.assertNotIn("NMAX 155", referencias)

    def test_cp_hu12_07_filtro_cilindraje_rango_min_y_max(self):
        """CP-HU12-07 · Unitaria — happy path · CA-02
        Con cilindraje_min=150 y cilindraje_max=300 deben aparecer las motos
        dentro de ese rango: FZ 25 (250 cc) y NMAX 155 (155 cc).
        Resultado esperado: HTTP 200 · FZ 25 y NMAX 155 presentes."""
        response = self.client.get(self.url, {"cilindraje_min": 150, "cilindraje_max": 300})
        self.assertEqual(response.status_code, 200)
        referencias = [m["referencia"] for m in response.data]
        self.assertIn("FZ 25", referencias)
        self.assertIn("NMAX 155", referencias)
        self.assertNotIn("XTZ 125", referencias)
        self.assertNotIn("MT-07", referencias)

    def test_cp_hu12_08_filtro_cilindraje_sin_coincidencias_retorna_lista_vacia(self):
        """CP-HU12-08 · Unitaria — flujo alternativo · CA-02
        Un rango de cilindraje donde no hay ninguna moto debe devolver lista vacía.
        Resultado esperado: HTTP 200 · lista vacía []."""
        response = self.client.get(self.url, {"cilindraje_min": 1000, "cilindraje_max": 2000})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    # ── CA-03 · Filtro por tipo ───────────────────────────────────────────────

    def test_cp_hu12_09_filtro_tipo_retorna_solo_ese_tipo(self):
        """CP-HU12-09 · Unitaria — happy path · CA-03
        Filtrar por tipo DEPORTIVA debe retornar FZ 25 y MT-07 solamente,
        excluyendo TODOTERRENO y AUTOMATICA.
        Resultado esperado: HTTP 200 · solo motos de tipo DEPORTIVA."""
        response = self.client.get(self.url, {"tipo": "DEPORTIVA"})
        self.assertEqual(response.status_code, 200)
        referencias = [m["referencia"] for m in response.data]
        self.assertIn("FZ 25", referencias)
        self.assertIn("MT-07", referencias)
        self.assertNotIn("XTZ 125", referencias)
        self.assertNotIn("NMAX 155", referencias)

    def test_cp_hu12_10_filtro_tipo_invalido_retorna_lista_vacia(self):
        """CP-HU12-10 · Unitaria — flujo alternativo · CA-03
        Un tipo que no existe en las opciones válidas no debe causar error;
        el backend lo ignora y retorna lista vacía.
        Resultado esperado: HTTP 200 · lista vacía []."""
        response = self.client.get(self.url, {"tipo": "VOLADORA"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    # ── CA-04 · Combinación de filtros (actualización dinámica) ──────────────

    def test_cp_hu12_11_combinacion_referencia_y_tipo(self):
        """CP-HU12-11 · Integración — happy path · CA-04
        Combinar referencia='MT' y tipo='DEPORTIVA' debe retornar solo la MT-07,
        validando que los filtros múltiples se aplican simultáneamente.
        Resultado esperado: HTTP 200 · solo MT-07."""
        response = self.client.get(self.url, {"referencia": "MT", "tipo": "DEPORTIVA"})
        self.assertEqual(response.status_code, 200)
        referencias = [m["referencia"] for m in response.data]
        self.assertIn("MT-07", referencias)
        self.assertNotIn("FZ 25", referencias)

    def test_cp_hu12_12_combinacion_tipo_y_cilindraje_min(self):
        """CP-HU12-12 · Integración — happy path · CA-04
        Combinar tipo='DEPORTIVA' y cilindraje_min=500 debe retornar solo
        la MT-07 (689 cc), ya que FZ 25 (250 cc) no supera el mínimo.
        Resultado esperado: HTTP 200 · solo MT-07."""
        response = self.client.get(self.url, {"tipo": "DEPORTIVA", "cilindraje_min": 500})
        self.assertEqual(response.status_code, 200)
        referencias = [m["referencia"] for m in response.data]
        self.assertIn("MT-07", referencias)
        self.assertNotIn("FZ 25", referencias)

    def test_cp_hu12_13_combinacion_tres_filtros_sin_resultado(self):
        """CP-HU12-13 · Integración — flujo alternativo · CA-04
        Aplicar referencia='XTZ', tipo='DEPORTIVA' y cilindraje_max=200
        no debe coincidir con ninguna moto (XTZ 125 es TODOTERRENO, no DEPORTIVA).
        Resultado esperado: HTTP 200 · lista vacía []."""
        response = self.client.get(
            self.url,
            {"referencia": "XTZ", "tipo": "DEPORTIVA", "cilindraje_max": 200},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_cp_hu12_14_sin_filtros_retorna_todo_el_catalogo_activo(self):
        """CP-HU12-14 · Unitaria — happy path · CA-04
        Sin parámetros de filtro el endpoint retorna todas las motos activas,
        confirmando que los filtros son completamente opcionales.
        Resultado esperado: HTTP 200 · las 4 motos activas del setUp."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 4)
        referencias = [m["referencia"] for m in response.data]
        self.assertNotIn("FZ inactiva", referencias)
