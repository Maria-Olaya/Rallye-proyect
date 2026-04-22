# catalog/tests.py

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from catalog.models import CotizacionMotocicleta, Motocicleta
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


class CotizarMotocicletaTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("cotizar_moto")
        self.local = make_local()
        self.motocicleta = Motocicleta.objects.create(
            referencia="FZ 150",
            anio=2026,
            tipo="URBANA",
            cilindraje=150,
            precio=Decimal("10000000.00"),
            caracteristicas="Moto urbana para uso diario.",
            activa=True,
        )

    def _payload_valido(self):
        return {
            "motocicleta_id": self.motocicleta.id,
            "cliente_nombre": "Juan Perez",
            "cliente_correo": "juan@test.com",
            "cliente_telefono": "3004567890",
            "comentario": "Deseo financiar la compra",
        }

    def test_cp_hu10_01_crea_cotizacion_con_desglose_y_radicado_sin_local(self):
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            response = self.client.post(self.url, self._payload_valido(), format="json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["radicado"].startswith("COT-"))
        self.assertEqual(response.data["precio_base"], "10000000.00")
        self.assertEqual(response.data["impuestos_estimados"], "1900000.00")
        self.assertEqual(response.data["tramites_estimados"], "800000.00")
        self.assertEqual(response.data["total_estimado"], "12700000.00")
        self.assertIsNone(response.data["local"])
        self.assertIn("https://wa.me/573113252436", response.data["whatsapp_url"])
        self.assertIn(response.data["radicado"], response.data["whatsapp_url"])
        self.assertEqual(CotizacionMotocicleta.objects.count(), 1)

    def test_cp_hu10_02_guarda_datos_correctos_en_bd(self):
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            self.client.post(self.url, self._payload_valido(), format="json")

        cotizacion = CotizacionMotocicleta.objects.get()
        self.assertEqual(cotizacion.motocicleta, self.motocicleta)
        self.assertIsNone(cotizacion.local)
        self.assertEqual(cotizacion.cliente_nombre, "Juan Perez")
        self.assertEqual(cotizacion.cliente_correo, "juan@test.com")
        self.assertEqual(cotizacion.cliente_telefono, "3004567890")
        self.assertEqual(cotizacion.total_estimado, Decimal("12700000.00"))

    def test_cp_hu10_03_correo_se_envia_si_cliente_ingresa_email(self):
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            response = self.client.post(self.url, self._payload_valido(), format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertIn(response.data["radicado"], correo.subject)
        self.assertEqual(correo.to, ["juan@test.com"])

        cotizacion = CotizacionMotocicleta.objects.get()
        self.assertTrue(cotizacion.correo_cotizacion_enviado)
        self.assertIsNotNone(cotizacion.fecha_envio_cotizacion)

    def test_cp_hu10_04_no_envia_correo_si_no_hay_email(self):
        payload = self._payload_valido()
        payload["cliente_correo"] = ""

        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 0)
        cotizacion = CotizacionMotocicleta.objects.get()
        self.assertFalse(cotizacion.correo_cotizacion_enviado)
        self.assertIsNone(cotizacion.fecha_envio_cotizacion)

    def test_cp_hu10_05_motocicleta_inexistente_retorna_400(self):
        payload = self._payload_valido()
        payload["motocicleta_id"] = 99999

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("motocicleta_id", response.data)
        self.assertFalse(CotizacionMotocicleta.objects.exists())

    def test_cp_hu10_06_motocicleta_inactiva_retorna_400(self):
        self.motocicleta.activa = False
        self.motocicleta.save(update_fields=["activa"])

        response = self.client.post(self.url, self._payload_valido(), format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("motocicleta_id", response.data)

    def test_cp_hu10_07_local_inactivo_retorna_400_si_se_envia(self):
        self.local.activo = False
        self.local.save(update_fields=["activo"])
        payload = self._payload_valido()
        payload["local_id"] = self.local.id

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("local_id", response.data)

    def test_cp_hu10_08_con_local_retorna_whatsapp(self):
        payload = self._payload_valido()
        payload["local_id"] = self.local.id

        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["local"]["id"], self.local.id)
        self.assertIn("https://wa.me/573001234567", response.data["whatsapp_url"])
        self.assertIn(response.data["radicado"], response.data["whatsapp_url"])

    def test_cp_hu10_09_usuario_autenticado_queda_asociado(self):
        admin = make_admin(self.local)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(admin)}")

        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            response = self.client.post(self.url, self._payload_valido(), format="json")

        self.assertEqual(response.status_code, 201)
        cotizacion = CotizacionMotocicleta.objects.get()
        self.assertEqual(cotizacion.usuario, admin)

    def test_cp_hu10_10_usuario_anonimo_puede_cotizar(self):
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            response = self.client.post(self.url, self._payload_valido(), format="json")

        self.assertEqual(response.status_code, 201)
        cotizacion = CotizacionMotocicleta.objects.get()
        self.assertIsNone(cotizacion.usuario)

    def test_cp_hu10_11_campos_texto_se_normalizan(self):
        payload = self._payload_valido()
        payload["cliente_nombre"] = "  Juan Perez  "
        payload["cliente_telefono"] = " 3004567890 "
        payload["comentario"] = "  Quiero entrega inmediata  "

        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            self.client.post(self.url, payload, format="json")

        cotizacion = CotizacionMotocicleta.objects.get()
        self.assertEqual(cotizacion.cliente_nombre, "Juan Perez")
        self.assertEqual(cotizacion.cliente_telefono, "3004567890")
        self.assertEqual(cotizacion.comentario, "Quiero entrega inmediata")

    def test_cp_hu10_12_radicados_son_unicos(self):
        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            response_1 = self.client.post(self.url, self._payload_valido(), format="json")
            response_2 = self.client.post(self.url, self._payload_valido(), format="json")

        self.assertEqual(response_1.status_code, 201)
        self.assertEqual(response_2.status_code, 201)
        self.assertNotEqual(response_1.data["radicado"], response_2.data["radicado"])


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


# ── HU-14 · Editar motocicleta ───────────────────────────────────────────────


class EditarMotocicletaTest(TestCase):
    """
    Cubre los criterios de aceptación de HU-14:
      CA-01  El administrador puede modificar los datos de la motocicleta.
      CA-02  Los cambios se reflejan en el catálogo público.
      CA-03  La información actualizada se guarda en la base de datos.
    """

    def setUp(self):
        self.client = APIClient()
        self.local = make_local()
        self.admin = make_admin(self.local)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(self.admin)}")

        self.moto = Motocicleta.objects.create(
            referencia="FZ 25",
            anio=2022,
            tipo="DEPORTIVA",
            cilindraje=250,
            precio="12500000.00",
            caracteristicas="Motor monocilíndrico original.",
            activa=True,
        )
        self.url_editar = f"/api/catalog/motocicletas/{self.moto.pk}/editar/"
        self.url_catalogo = "/api/catalog/motocicletas/"

    def _payload_completo(self, **overrides):
        base = {
            "referencia": "FZ 25",
            "anio": 2023,
            "tipo": "DEPORTIVA",
            "cilindraje": 250,
            "precio": "13000000.00",
            "caracteristicas": "Motor monocilíndrico actualizado.",
        }
        base.update(overrides)
        return base

    # ── GET — cargar datos actuales ──────────────────────────────────────────

    def test_cp_hu14_01_get_retorna_datos_actuales_de_la_moto(self):
        """CP-HU14-01 · Unitaria — flujo feliz · CA-01
        GET al endpoint de edición debe retornar los datos actuales de la moto
        para que el formulario pueda precargarse correctamente.
        Resultado esperado: HTTP 200 · datos coinciden con los de la BD."""
        response = self.client.get(self.url_editar)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["referencia"], "FZ 25")
        self.assertEqual(response.data["cilindraje"], 250)
        self.assertEqual(response.data["tipo"], "DEPORTIVA")

    def test_cp_hu14_02_get_moto_inexistente_retorna_404(self):
        """CP-HU14-02 · Unitaria — flujo alternativo · CA-01
        GET con un pk que no existe debe retornar 404, no un error del servidor.
        Resultado esperado: HTTP 404."""
        response = self.client.get("/api/catalog/motocicletas/9999/editar/")
        self.assertEqual(response.status_code, 404)

    # ── PUT — actualización completa ─────────────────────────────────────────

    def test_cp_hu14_03_put_actualiza_datos_correctamente(self):
        """CP-HU14-03 · Unitaria — flujo feliz · CA-01 · CA-03
        PUT con datos válidos debe actualizar todos los campos de la moto
        y retornar HTTP 200 con el mensaje de confirmación.
        Resultado esperado: HTTP 200 · campos actualizados en BD."""
        response = self.client.put(
            self.url_editar,
            self._payload_completo(anio=2024, cilindraje=300),
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.anio, 2024)
        self.assertEqual(self.moto.cilindraje, 300)

    def test_cp_hu14_04_put_cambios_se_reflejan_en_catalogo_publico(self):
        """CP-HU14-04 · Integración — flujo feliz · CA-02
        Tras un PUT exitoso, el catálogo público debe mostrar los datos
        actualizados sin necesidad de reiniciar el servidor.
        Resultado esperado: HTTP 200 · catálogo retorna el nuevo precio."""
        nuevo_precio = "15000000.00"
        self.client.put(
            self.url_editar,
            self._payload_completo(precio=nuevo_precio),
            format="json",
        )
        catalogo = self.client.get(self.url_catalogo)
        moto = next(m for m in catalogo.data if m["referencia"] == "FZ 25")
        self.assertIn("15.000.000", moto["precio_display"])

    def test_cp_hu14_05_put_moto_inexistente_retorna_404(self):
        """CP-HU14-05 · Unitaria — flujo alternativo · CA-01
        PUT sobre un pk inexistente debe retornar 404.
        Resultado esperado: HTTP 404."""
        response = self.client.put(
            "/api/catalog/motocicletas/9999/editar/",
            self._payload_completo(),
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_cp_hu14_06_put_sin_autenticacion_retorna_401(self):
        """CP-HU14-06 · Control de acceso · CA-01
        PUT sin token JWT debe ser rechazado con 401 y la moto no debe
        modificarse en la base de datos.
        Resultado esperado: HTTP 401 · datos originales intactos en BD."""
        self.client.credentials()
        response = self.client.put(
            self.url_editar,
            self._payload_completo(referencia="HACK"),
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.referencia, "FZ 25")

    def test_cp_hu14_07_put_cilindraje_invalido_retorna_400(self):
        """CP-HU14-07 · Caja negra — validación · CA-01
        PUT con cilindraje = 0 debe retornar 400 y no modificar la moto.
        Resultado esperado: HTTP 400 · cilindraje original intacto en BD."""
        response = self.client.put(
            self.url_editar,
            self._payload_completo(cilindraje=0),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.cilindraje, 250)

    def test_cp_hu14_08_put_precio_negativo_retorna_400(self):
        """CP-HU14-08 · Caja negra — validación · CA-01
        PUT con precio negativo debe retornar 400 y no modificar la moto.
        Resultado esperado: HTTP 400 · precio original intacto en BD."""
        response = self.client.put(
            self.url_editar,
            self._payload_completo(precio="-500.00"),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.precio, 12500000)

    def test_cp_hu14_09_put_anio_invalido_retorna_400(self):
        """CP-HU14-09 · Caja negra — validación · CA-01
        PUT con año fuera del rango válido debe retornar 400.
        Resultado esperado: HTTP 400 · año original intacto en BD."""
        response = self.client.put(
            self.url_editar,
            self._payload_completo(anio=1800),
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.anio, 2022)

    # ── PATCH — actualización parcial ────────────────────────────────────────

    def test_cp_hu14_10_patch_actualiza_solo_campo_enviado(self):
        """CP-HU14-10 · Unitaria — flujo feliz · CA-01 · CA-03
        PATCH con un solo campo debe actualizar únicamente ese campo y dejar
        los demás intactos en la base de datos.
        Resultado esperado: HTTP 200 · solo las características cambian."""
        nueva_desc = "Descripción actualizada vía PATCH."
        response = self.client.patch(
            self.url_editar,
            {"caracteristicas": nueva_desc},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.caracteristicas, nueva_desc)
        self.assertEqual(self.moto.cilindraje, 250)  # sin cambios

    def test_cp_hu14_11_patch_sin_autenticacion_retorna_401(self):
        """CP-HU14-11 · Control de acceso · CA-01
        PATCH sin token JWT debe retornar 401 y la moto no debe modificarse.
        Resultado esperado: HTTP 401 · datos originales intactos en BD."""
        self.client.credentials()
        response = self.client.patch(
            self.url_editar,
            {"referencia": "HACK"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.referencia, "FZ 25")

    # ── Integración BD ───────────────────────────────────────────────────────

    def test_cp_hu14_12_datos_persisten_correctamente_en_bd(self):
        """CP-HU14-12 · Integración · CA-03
        Tras un PUT exitoso, todos los campos modificados deben persistir
        correctamente en la base de datos tras hacer refresh_from_db.
        Resultado esperado: HTTP 200 · todos los campos nuevos en BD."""
        self.client.put(
            self.url_editar,
            self._payload_completo(
                referencia="FZ 25 Pro",
                anio=2025,
                tipo="URBANA",
                cilindraje=300,
                precio="14000000.00",
                caracteristicas="Versión Pro actualizada.",
            ),
            format="json",
        )
        self.moto.refresh_from_db()
        self.assertEqual(self.moto.referencia, "FZ 25 Pro")
        self.assertEqual(self.moto.anio, 2025)
        self.assertEqual(self.moto.tipo, "URBANA")
        self.assertEqual(self.moto.cilindraje, 300)
        self.assertEqual(self.moto.precio, 14000000)
        self.assertEqual(self.moto.caracteristicas, "Versión Pro actualizada.")
        self.assertEqual(self.moto.marca, "Yamaha")  # campo no editable, intacto


# ── HU-15 · Desactivar motocicleta ────────────────────────────────────────────


class DesactivarMotocicletaTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.local = make_local()
        self.admin = make_admin(self.local)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(self.admin)}")
        self.moto = Motocicleta.objects.create(
            referencia="MT-03",
            anio=2024,
            tipo="DEPORTIVA",
            cilindraje=321,
            precio="15000000.00",
            caracteristicas="Moto deportiva de media cilindrada.",
            activa=True,
        )

    def _url(self, pk=None):
        pk = pk or self.moto.pk
        return f"/api/catalog/motocicletas/{pk}/desactivar/"

    def test_cp_hu15_01_admin_desactiva_moto_correctamente(self):
        """CP-HU15-01 · Caja negra — flujo feliz · CA-01"""
        response = self.client.patch(self._url(), format="json")
        self.assertEqual(response.status_code, 200)
        self.moto.refresh_from_db()
        self.assertFalse(self.moto.activa)
        self.assertIn("mensaje", response.data)

    def test_cp_hu15_02_moto_desactivada_no_aparece_en_catalogo_publico(self):
        """CP-HU15-02 · Integración — visibilidad · CA-01"""
        self.client.patch(self._url(), format="json")
        public_client = APIClient()
        response = public_client.get("/api/catalog/motocicletas/", format="json")
        self.assertEqual(response.status_code, 200)
        ids = [m["id"] for m in response.data]
        self.assertNotIn(self.moto.pk, ids)

    def test_cp_hu15_03_moto_desactivada_permanece_en_base_de_datos(self):
        """CP-HU15-03 · Base de datos — registro · CA-01"""
        self.client.patch(self._url(), format="json")
        self.assertTrue(Motocicleta.objects.filter(pk=self.moto.pk).exists())
        self.moto.refresh_from_db()
        self.assertFalse(self.moto.activa)

    def test_cp_hu15_04_sin_autenticacion_retorna_401(self):
        """CP-HU15-04 · Control de acceso · CA-01"""
        self.client.credentials()
        response = self.client.patch(self._url(), format="json")
        self.assertEqual(response.status_code, 401)
        self.moto.refresh_from_db()
        self.assertTrue(self.moto.activa)

    def test_cp_hu15_05_moto_inexistente_retorna_404(self):
        """CP-HU15-05 · Caja negra — ID inválido · CA-01"""
        response = self.client.patch(self._url(pk=99999), format="json")
        self.assertEqual(response.status_code, 404)

    def test_cp_hu15_06_desactivar_moto_ya_inactiva_retorna_400(self):
        """CP-HU15-06 · Caja negra — estado duplicado · CA-01"""
        self.moto.activa = False
        self.moto.save()
        response = self.client.patch(self._url(), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_cp_hu15_07_moto_activa_sigue_visible_en_catalogo(self):
        """CP-HU15-07 · Integración — otra moto no se ve afectada · CA-01"""
        otra_moto = Motocicleta.objects.create(
            referencia="FZ 25",
            anio=2023,
            tipo="URBANA",
            cilindraje=250,
            precio="12000000.00",
            caracteristicas="Moto urbana.",
            activa=True,
        )
        self.client.patch(self._url(), format="json")
        public_client = APIClient()
        response = public_client.get("/api/catalog/motocicletas/", format="json")
        ids = [m["id"] for m in response.data]
        self.assertIn(otra_moto.pk, ids)
        self.assertNotIn(self.moto.pk, ids)


# ── HU-15 · Activar motocicleta ───────────────────────────────────────────────


class ActivarMotocicletaTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.local = make_local()
        self.admin = make_admin(self.local)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(self.admin)}")
        self.moto = Motocicleta.objects.create(
            referencia="MT-03",
            anio=2024,
            tipo="DEPORTIVA",
            cilindraje=321,
            precio="15000000.00",
            caracteristicas="Moto deportiva de media cilindrada.",
            activa=False,  # empieza inactiva
        )

    def _url(self, pk=None):
        pk = pk or self.moto.pk
        return f"/api/catalog/motocicletas/{pk}/activar/"

    def test_cp_hu15_08_admin_activa_moto_correctamente(self):
        """CP-HU15-08 · Caja negra — flujo feliz"""
        response = self.client.patch(self._url(), format="json")
        self.assertEqual(response.status_code, 200)
        self.moto.refresh_from_db()
        self.assertTrue(self.moto.activa)
        self.assertIn("mensaje", response.data)

    def test_cp_hu15_09_moto_activada_aparece_en_catalogo_publico(self):
        """CP-HU15-09 · Integración — visibilidad"""
        self.client.patch(self._url(), format="json")
        public_client = APIClient()
        response = public_client.get("/api/catalog/motocicletas/", format="json")
        ids = [m["id"] for m in response.data]
        self.assertIn(self.moto.pk, ids)

    def test_cp_hu15_10_activar_moto_ya_activa_retorna_400(self):
        """CP-HU15-10 · Caja negra — estado duplicado"""
        self.moto.activa = True
        self.moto.save()
        response = self.client.patch(self._url(), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_cp_hu15_11_sin_autenticacion_retorna_401(self):
        """CP-HU15-11 · Control de acceso"""
        self.client.credentials()
        response = self.client.patch(self._url(), format="json")
        self.assertEqual(response.status_code, 401)
        self.moto.refresh_from_db()
        self.assertFalse(self.moto.activa)

    def test_cp_hu15_12_moto_inexistente_retorna_404(self):
        """CP-HU15-12 · Caja negra — ID inválido"""
        response = self.client.patch(self._url(pk=99999), format="json")
        self.assertEqual(response.status_code, 404)


# ── HU-15 · Listado admin ─────────────────────────────────────────────────────


class ListadoAdminMotocicletasTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.local = make_local()
        self.admin = make_admin(self.local)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(self.admin)}")
        self.moto_activa = Motocicleta.objects.create(
            referencia="MT-03",
            anio=2024,
            tipo="DEPORTIVA",
            cilindraje=321,
            precio="15000000.00",
            caracteristicas="Moto activa.",
            activa=True,
        )
        self.moto_inactiva = Motocicleta.objects.create(
            referencia="FZ 150",
            anio=2023,
            tipo="URBANA",
            cilindraje=150,
            precio="9000000.00",
            caracteristicas="Moto inactiva.",
            activa=False,
        )

    def test_cp_hu15_13_admin_ve_todas_las_motos(self):
        """CP-HU15-13 · Admin ve activas e inactivas"""
        response = self.client.get("/api/catalog/motocicletas/admin/")
        self.assertEqual(response.status_code, 200)
        ids = [m["id"] for m in response.data]
        self.assertIn(self.moto_activa.pk, ids)
        self.assertIn(self.moto_inactiva.pk, ids)

    def test_cp_hu15_14_sin_autenticacion_retorna_401(self):
        """CP-HU15-14 · Control de acceso"""
        self.client.credentials()
        response = self.client.get("/api/catalog/motocicletas/admin/")
        self.assertEqual(response.status_code, 401)

    def test_cp_hu15_15_respuesta_incluye_campo_activa(self):
        """CP-HU15-15 · El serializer retorna el campo activa"""
        response = self.client.get("/api/catalog/motocicletas/admin/")
        self.assertEqual(response.status_code, 200)
        for m in response.data:
            self.assertIn("activa", m)

# ── HU-09: Consultar repuestos guiado ─────────────────────────────────────────


class ModelosMotoViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/catalog/repuestos/modelos/"
        Motocicleta.objects.create(
            referencia="FZ 25", anio=2023, tipo="DEPORTIVA",
            cilindraje=250, precio="12500000.00",
            caracteristicas="Motor monocilíndrico.", activa=True,
        )
        Motocicleta.objects.create(
            referencia="FZ 25", anio=2024, tipo="DEPORTIVA",
            cilindraje=250, precio="13000000.00",
            caracteristicas="Motor monocilíndrico.", activa=True,
        )
        Motocicleta.objects.create(
            referencia="MT-07", anio=2024, tipo="DEPORTIVA",
            cilindraje=689, precio="28000000.00",
            caracteristicas="Motor bicilíndrico.", activa=True,
        )
        Motocicleta.objects.create(
            referencia="YBR 125", anio=2020, tipo="URBANA",
            cilindraje=125, precio="8000000.00",
            caracteristicas="Moto básica.", activa=False,
        )

    def test_cp_rep_01_retorna_modelos_unicos_de_motos_activas(self):
        """CP-REP-01 · Unitaria — flujo feliz
        Debe retornar referencias únicas de motos activas.
        FZ 25 existe dos veces pero debe aparecer solo una vez.
        Resultado esperado: HTTP 200 · ['FZ 25', 'MT-07'] sin duplicados."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        modelos = response.data["modelos"]
        self.assertIn("FZ 25", modelos)
        self.assertIn("MT-07", modelos)
        self.assertEqual(modelos.count("FZ 25"), 1)

    def test_cp_rep_02_no_retorna_motos_inactivas(self):
        """CP-REP-02 · Unitaria — control de visibilidad
        Las motos inactivas no deben aparecer en la lista de modelos.
        Resultado esperado: HTTP 200 · 'YBR 125' ausente."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("YBR 125", response.data["modelos"])

    def test_cp_rep_03_sin_motos_activas_retorna_lista_vacia(self):
        """CP-REP-03 · Unitaria — flujo alternativo
        Si no hay motos activas, debe retornar lista vacía, no error.
        Resultado esperado: HTTP 200 · modelos: []"""
        Motocicleta.objects.update(activa=False)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["modelos"], [])

    def test_cp_rep_04_endpoint_es_publico_sin_autenticacion(self):
        """CP-REP-04 · Control de acceso
        El endpoint no requiere autenticación.
        Resultado esperado: HTTP 200 sin token."""
        self.client.credentials()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_cp_rep_05_modelos_retornados_ordenados_alfabeticamente(self):
        """CP-REP-05 · Unitaria — orden
        Los modelos deben retornarse ordenados alfabéticamente.
        Resultado esperado: HTTP 200 · FZ 25 antes que MT-07."""
        response = self.client.get(self.url)
        modelos = response.data["modelos"]
        self.assertEqual(modelos, sorted(modelos))


class AniosModeloViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        Motocicleta.objects.create(
            referencia="FZ 25", anio=2022, tipo="DEPORTIVA",
            cilindraje=250, precio="11000000.00",
            caracteristicas="Versión 2022.", activa=True,
        )
        Motocicleta.objects.create(
            referencia="FZ 25", anio=2023, tipo="DEPORTIVA",
            cilindraje=250, precio="12500000.00",
            caracteristicas="Versión 2023.", activa=True,
        )
        Motocicleta.objects.create(
            referencia="FZ 25", anio=2020, tipo="DEPORTIVA",
            cilindraje=250, precio="10000000.00",
            caracteristicas="Versión inactiva.", activa=False,
        )

    def _url(self, referencia):
        return f"/api/catalog/repuestos/modelos/{referencia}/anios/"

    def test_cp_rep_06_retorna_anios_del_modelo_activo(self):
        """CP-REP-06 · Unitaria — flujo feliz
        Debe retornar los años de las motos activas con esa referencia.
        Resultado esperado: HTTP 200 · [2023, 2022]."""
        response = self.client.get(self._url("FZ 25"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(2022, response.data["anios"])
        self.assertIn(2023, response.data["anios"])

    def test_cp_rep_07_no_retorna_anios_de_motos_inactivas(self):
        """CP-REP-07 · Unitaria — control de visibilidad
        El año 2020 corresponde a una moto inactiva y no debe aparecer.
        Resultado esperado: HTTP 200 · 2020 ausente en anios."""
        response = self.client.get(self._url("FZ 25"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(2020, response.data["anios"])

    def test_cp_rep_08_anios_retornados_en_orden_descendente(self):
        """CP-REP-08 · Unitaria — orden
        Los años más recientes deben aparecer primero.
        Resultado esperado: HTTP 200 · 2023 antes que 2022."""
        response = self.client.get(self._url("FZ 25"))
        anios = response.data["anios"]
        self.assertEqual(anios, sorted(anios, reverse=True))

    def test_cp_rep_09_modelo_inexistente_retorna_404(self):
        """CP-REP-09 · Unitaria — flujo alternativo
        Un modelo que no existe debe retornar 404.
        Resultado esperado: HTTP 404."""
        response = self.client.get(self._url("NOEXISTE"))
        self.assertEqual(response.status_code, 404)

    def test_cp_rep_10_retorna_nombre_del_modelo_en_respuesta(self):
        """CP-REP-10 · Unitaria — estructura de respuesta
        La respuesta debe incluir el campo 'modelo'.
        Resultado esperado: HTTP 200 · modelo == 'FZ 25'."""
        response = self.client.get(self._url("FZ 25"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["modelo"], "FZ 25")

    def test_cp_rep_11_endpoint_es_publico(self):
        """CP-REP-11 · Control de acceso
        No requiere autenticación.
        Resultado esperado: HTTP 200 sin token."""
        self.client.credentials()
        response = self.client.get(self._url("FZ 25"))
        self.assertEqual(response.status_code, 200)


class RegistrarConsultaRepuestoViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/catalog/repuestos/consulta/"
        self.local = make_local()

    def _payload_valido(self):
        return {
            "repuesto_nombre": "Filtro de aire",
            "repuesto_referencia": "5VK-14451-00",
            "modelo_moto": "Yamaha FZ 25 2023",
            "local": self.local.id,
        }

    def test_cp_rep_12_consulta_valida_queda_guardada_en_bd(self):
        """CP-REP-12 · Integración — flujo feliz
        Una consulta válida debe persistir en la tabla ConsultaRepuesto.
        Resultado esperado: HTTP 201 · un registro en BD."""
        from catalog.models import ConsultaRepuesto
        response = self.client.post(self.url, self._payload_valido(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ConsultaRepuesto.objects.count(), 1)

    def test_cp_rep_13_bd_guarda_datos_correctos(self):
        """CP-REP-13 · Integración — integridad de datos
        Los campos guardados deben coincidir con el payload enviado.
        Resultado esperado: HTTP 201 · campos en BD iguales al payload."""
        from catalog.models import ConsultaRepuesto
        self.client.post(self.url, self._payload_valido(), format="json")
        consulta = ConsultaRepuesto.objects.get()
        self.assertEqual(consulta.repuesto_nombre, "Filtro de aire")
        self.assertEqual(consulta.repuesto_referencia, "5VK-14451-00")
        self.assertEqual(consulta.modelo_moto, "Yamaha FZ 25 2023")
        self.assertEqual(consulta.local_id, self.local.id)

    def test_cp_rep_14_respuesta_incluye_url_whatsapp(self):
        """CP-REP-14 · Unitaria — estructura de respuesta
        La respuesta debe incluir whatsapp_url con 'wa.me'.
        Resultado esperado: HTTP 201 · whatsapp_url contiene 'wa.me'."""
        response = self.client.post(self.url, self._payload_valido(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data["whatsapp_url"])
        self.assertIn("wa.me", response.data["whatsapp_url"])

    def test_cp_rep_15_whatsapp_url_contiene_nombre_repuesto(self):
        """CP-REP-15 · Unitaria — contenido del mensaje WhatsApp
        La URL de WhatsApp debe incluir el nombre del repuesto.
        Resultado esperado: HTTP 201 · 'Filtro' en whatsapp_url."""
        response = self.client.post(self.url, self._payload_valido(), format="json")
        self.assertIn("Filtro", response.data["whatsapp_url"])

    def test_cp_rep_16_whatsapp_url_contiene_telefono_colombia(self):
        """CP-REP-16 · Unitaria — formato de teléfono
        El teléfono debe tener prefijo 57 en la URL de WhatsApp.
        Resultado esperado: HTTP 201 · URL contiene '573001234567'."""
        response = self.client.post(self.url, self._payload_valido(), format="json")
        self.assertIn("573001234567", response.data["whatsapp_url"])

    def test_cp_rep_17_repuesto_nombre_vacio_retorna_400(self):
        """CP-REP-17 · Caja negra — validación campo obligatorio
        El nombre del repuesto vacío debe retornar 400.
        Resultado esperado: HTTP 400 · sin registros en BD."""
        from catalog.models import ConsultaRepuesto
        payload = self._payload_valido()
        payload["repuesto_nombre"] = ""
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ConsultaRepuesto.objects.count(), 0)

    def test_cp_rep_18_sin_local_no_genera_whatsapp_url(self):
        """CP-REP-18 · Unitaria — flujo alternativo sin local
        Sin local, la consulta se guarda pero whatsapp_url es None.
        Resultado esperado: HTTP 201 · whatsapp_url == None."""
        from catalog.models import ConsultaRepuesto
        payload = self._payload_valido()
        del payload["local"]
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data["whatsapp_url"])
        self.assertEqual(ConsultaRepuesto.objects.count(), 1)

    def test_cp_rep_19_consulta_guarda_fecha_automaticamente(self):
        """CP-REP-19 · Unitaria — auto campos
        El campo 'fecha' debe asignarse automáticamente.
        Resultado esperado: HTTP 201 · consulta.fecha == hoy."""
        from catalog.models import ConsultaRepuesto
        from datetime import date
        self.client.post(self.url, self._payload_valido(), format="json")
        consulta = ConsultaRepuesto.objects.get()
        self.assertEqual(consulta.fecha, date.today())

    def test_cp_rep_20_respuesta_incluye_info_del_local(self):
        """CP-REP-20 · Unitaria — estructura de respuesta
        La respuesta debe incluir el objeto 'local' con nombre.
        Resultado esperado: HTTP 201 · local.nombre == 'Local Test'."""
        response = self.client.post(self.url, self._payload_valido(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data["local"])
        self.assertEqual(response.data["local"]["nombre"], "Local Test")

    def test_cp_rep_21_endpoint_es_publico(self):
        """CP-REP-21 · Control de acceso
        Cualquier usuario puede registrar una consulta sin token.
        Resultado esperado: HTTP 201 sin token JWT."""
        self.client.credentials()
        response = self.client.post(self.url, self._payload_valido(), format="json")
        self.assertEqual(response.status_code, 201)

    def test_cp_rep_22_multiples_consultas_se_guardan_independientemente(self):
        """CP-REP-22 · Integración — múltiples registros
        Dos consultas distintas deben generar dos registros en BD.
        Resultado esperado: ConsultaRepuesto.count() == 2."""
        from catalog.models import ConsultaRepuesto
        self.client.post(self.url, self._payload_valido(), format="json")
        payload2 = self._payload_valido()
        payload2["repuesto_nombre"] = "Pastillas de freno"
        self.client.post(self.url, payload2, format="json")
        self.assertEqual(ConsultaRepuesto.objects.count(), 2)