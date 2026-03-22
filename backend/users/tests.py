from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class HU07IniciarSesionTests(TestCase):
    """
    Casos de prueba para HU-07: Iniciar Sesión.

    Historia de usuario:
        Como administrador del local, quiero iniciar sesión en el sistema
        para acceder al panel administrativo.

    Criterios de aceptación:
        CA-01: El administrador puede ingresar sus credenciales (correo + password).
        CA-02: El sistema valida las credenciales ingresadas.
        CA-03: El acceso solo se permite a cuentas registradas y activas (no superusers).
        CA-04: Al iniciar sesión correctamente se accede al panel administrativo.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("api_login")
        self.logout_url = reverse("api_logout")

        self.admin = User.objects.create_user(
            username="admin_rallye",
            email="admin@rallyemotors.com.co",
            password="Segura123!",
        )
        self.admin_inactivo = User.objects.create_user(
            username="admin_inactivo",
            email="inactivo@rallyemotors.com.co",
            password="Segura123!",
            is_active=False,
        )
        self.superuser = User.objects.create_superuser(
            username="superuser",
            email="super@dev.com",
            password="Segura123!",
        )

    def _login(self, email="admin@rallyemotors.com.co", password="Segura123!"):
        return self.client.post(
            self.url,
            {"email": email, "password": password},
            format="json",
        )

    def _get_tokens(self, email="admin@rallyemotors.com.co", password="Segura123!"):
        response = self._login(email, password)
        return response.data["access"], response.data["refresh"]

    # ── CA-01: El administrador puede ingresar sus credenciales ──────────

    def test_cp01_login_exitoso_credenciales_correctas(self):
        """CP-01 · Flujo feliz — credenciales correctas → 200 + tokens + email."""
        response = self._login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["email"], "admin@rallyemotors.com.co")

    def test_cp02_login_retorna_jwt_valido(self):
        """CP-02 · Access token tiene formato JWT (3 segmentos)."""
        response = self._login()
        self.assertEqual(len(response.data["access"].split(".")), 3)

    def test_cp03_login_retorna_refresh_valido(self):
        """CP-03 · Refresh token tiene formato JWT (3 segmentos)."""
        response = self._login()
        self.assertEqual(len(response.data["refresh"].split(".")), 3)

    def test_cp04_login_respuesta_contiene_claves_correctas(self):
        """CP-04 · Respuesta exitosa tiene: access, refresh, email, local_id, local_nombre."""
        response = self._login()
        claves = set(response.data.keys())
        self.assertEqual(claves, {"access", "refresh", "email", "local_id", "local_nombre"})

    def test_cp05_login_local_es_none_sin_local_asignado(self):
        """CP-05 · local_id y local_nombre son null si el admin no tiene local."""
        response = self._login()
        self.assertIsNone(response.data["local_id"])
        self.assertIsNone(response.data["local_nombre"])

    # ── CA-02: El sistema valida las credenciales ────────────────────────

    def test_cp06_login_falla_password_incorrecto(self):
        """CP-06 · Password incorrecto → 400 con clave 'error'."""
        response = self._login(password="WrongPass999")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_cp07_login_falla_email_incorrecto(self):
        """CP-07 · Email que no existe → 400 con clave 'error'."""
        response = self._login(email="noexiste@rallye.com")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_cp08_login_falla_email_vacio(self):
        """CP-08 · Email vacío → 400."""
        response = self.client.post(self.url, {"email": "", "password": "Segura123!"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp09_login_falla_password_vacio(self):
        """CP-09 · Password vacío → 400."""
        response = self.client.post(self.url, {"email": "admin@rallyemotors.com.co", "password": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp10_login_falla_payload_vacio(self):
        """CP-10 · Payload vacío → 400."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp11_login_falla_metodo_get(self):
        """CP-11 · GET → 405."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cp12_login_error_no_revela_existencia_usuario(self):
        """CP-12 · Mismo mensaje de error para email inexistente y password incorrecto."""
        r1 = self._login(password="wrong")
        r2 = self._login(email="noexiste@rallye.com")
        self.assertEqual(r1.data["error"], r2.data["error"])

    def test_cp13_login_password_case_sensitive(self):
        """CP-13 · Password es case-sensitive."""
        response = self._login(password="segura123!")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── CA-03: Solo cuentas registradas y activas (no superusers) ────────

    def test_cp14_login_falla_cuenta_inactiva(self):
        """CP-14 · Cuenta desactivada → 400."""
        response = self._login(email="inactivo@rallyemotors.com.co")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp15_login_falla_superuser_no_puede_acceder(self):
        """CP-15 · Superuser no puede iniciar sesión por esta vía → 400."""
        response = self._login(email="super@dev.com")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_cp16_login_falla_email_no_registrado(self):
        """CP-16 · Email no registrado en BD → 400."""
        response = self._login(email="intruso@rallye.com")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── CA-04: Al iniciar sesión correctamente se accede al panel ─────────

    def test_cp17_token_valido_permite_acceso_endpoint_protegido(self):
        """CP-17 · Access token válido → endpoint protegido 200."""
        access, refresh = self._get_tokens()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(self.logout_url, {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cp18_acceso_sin_token_rechazado(self):
        """CP-18 · Sin token → 401."""
        self.client.credentials()
        response = self.client.post(self.logout_url, {"refresh": "fake"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cp19_logout_exitoso(self):
        """CP-19 · Logout correcto → 200 + mensaje."""
        access, refresh = self._get_tokens()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(self.logout_url, {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

    def test_cp20_logout_falla_sin_refresh(self):
        """CP-20 · Logout sin refresh → 400."""
        access, _ = self._get_tokens()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(self.logout_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp21_refresh_blacklisted_tras_logout(self):
        """CP-21 · Refresh en blacklist tras logout lanza TokenError."""
        from rest_framework_simplejwt.exceptions import TokenError

        access, refresh = self._get_tokens()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        self.client.post(self.logout_url, {"refresh": refresh}, format="json")

        with self.assertRaises(TokenError):
            RefreshToken(refresh)

    def test_cp22_dos_logins_generan_tokens_distintos(self):
        """CP-22 · Dos logins seguidos → tokens distintos."""
        r1 = self._login()
        r2 = self._login()
        self.assertNotEqual(r1.data["access"], r2.data["access"])
