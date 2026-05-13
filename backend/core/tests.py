from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from core.models import Local, Municipio, Sede

User = get_user_model()


def make_local():
    municipio = Municipio.objects.create(nombre="Medellin", departamento="Antioquia")
    sede = Sede.objects.create(nombre="Sede Centro", direccion="Calle 1", municipio=municipio)
    return Local.objects.create(
        nombre="Local Centro",
        sede=sede,
        direccion="Cra 50",
        telefono="3001234567",
        correo_admin="local@test.com",
        num_mecanicos=3,
    )


def make_admin(local):
    user = User.objects.create_user(
        username="admin1",
        email="admin@rallye.com",
        password="Segura123!",
        local=local,
    )
    return user


def get_token(user):
    return str(RefreshToken.for_user(user).access_token)


class LocalUpdateTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.local = make_local()
        self.admin = make_admin(self.local)
        self.url = f"/api/core/locales/{self.local.pk}/editar/"

    def test_admin_puede_actualizar_telefono(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(self.admin)}")
        resp = self.client.patch(self.url, {"telefono": "3119999999"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.local.refresh_from_db()
        self.assertEqual(self.local.telefono, "3119999999")

    def test_admin_puede_actualizar_descripcion(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(self.admin)}")
        resp = self.client.patch(self.url, {"descripcion": "Taller especializado"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.local.refresh_from_db()
        self.assertEqual(self.local.descripcion, "Taller especializado")

    def test_no_autenticado_recibe_401(self):
        resp = self.client.patch(self.url, {"telefono": "3119999999"}, format="json")
        self.assertEqual(resp.status_code, 401)

    def test_admin_otro_local_recibe_404(self):
        otro_local = make_local()
        otro_admin = User.objects.create_user(
            username="admin2",
            email="admin2@rallye.com",
            password="Segura123!",
            local=otro_local,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(otro_admin)}")
        resp = self.client.patch(self.url, {"telefono": "3119999999"}, format="json")
        self.assertEqual(resp.status_code, 404)

    def test_get_retorna_datos_actuales(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(self.admin)}")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["telefono"], "3001234567")

    def test_admin_puede_actualizar_horarios(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {get_token(self.admin)}")
        horarios = [
            {"dias": ["lun", "mar", "mie", "jue", "vie"], "apertura": "08:00", "cierre": "17:00"},
            {"dias": ["sab"], "apertura": "07:00", "cierre": "12:00"},
        ]
        resp = self.client.patch(self.url, {"horarios": horarios}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.local.refresh_from_db()
        self.assertEqual(len(self.local.horarios), 2)
        self.assertIn("lun", self.local.horarios[0]["dias"])






# ========== TESTS PARA HU-17: VISUALIZAR SEDES EN EL MAPA ==========

class MapaSedesTest(TestCase):
    def setUp(self):
        # Crear municipios y sedes con coordenadas (como se ve en el commit)
        self.municipio_bogota = Municipio.objects.create(
            nombre="Bogotá", departamento="Cundinamarca"
        )
        self.municipio_medellin = Municipio.objects.create(
            nombre="Medellín", departamento="Antioquia"
        )
        
        self.sede1 = Sede.objects.create(
            nombre="Sede Bogotá - Zona Centro",
            direccion="Carrera 7 # 32-45, Bogotá",
            municipio=self.municipio_bogota,
            lat=4.7110,
            lng=-74.0721,
            activa=True,
        )
        self.sede2 = Sede.objects.create(
            nombre="Sede Medellín - Centro",
            direccion="Carrera 49 # 52-36, Medellín",
            municipio=self.municipio_medellin,
            lat=6.2443,
            lng=-75.5812,
            activa=True,
        )

    def test_api_sedes_devuelve_todas_las_sedes_con_coordenadas(self):
        response = self.client.get("/api/core/sedes/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        for sede in response.data:
            self.assertIn("nombre", sede)
            self.assertIn("municipio_nombre", sede)
            self.assertIn("lat", sede)
            self.assertIn("lng", sede)
            self.assertIn("direccion", sede)
            self.assertIsNotNone(sede["lat"])
            self.assertIsNotNone(sede["lng"])
            # Opcional: verificar que sean números (strings convertibles)
            try:
                float(sede["lat"])
                float(sede["lng"])
            except (TypeError, ValueError):
                self.fail(f"lat/lng no numéricos: {sede['lat']}, {sede['lng']}")

    def test_vista_mapa_sedes_carga_template_correcto(self):
        """La URL /mapa/ debe mostrar la plantilla mapa_sedes.html."""
        response = self.client.get("/mapa/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mapa_sedes.html")

    def test_vista_mapa_sedes_contiene_elementos_para_leaflet(self):
        """Verifica que el HTML generado incluya el div del mapa y la llamada a la API."""
        response = self.client.get("/mapa/")
        content = response.content.decode("utf-8")
        # Debe existir el contenedor del mapa
        self.assertIn('<div id="mapa"', content)
        # Debe hacer fetch a la API de sedes
        self.assertIn("/api/core/sedes/", content)
        # Debe tener referencia a Leaflet CSS/JS
        self.assertIn("leaflet", content)
