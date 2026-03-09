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
        CA-01: El administrador puede ingresar sus credenciales.
        CA-02: El sistema valida las credenciales ingresadas.
        CA-03: El acceso solo se permite a cuentas registradas.
        CA-04: Al iniciar sesión correctamente se accede al panel administrativo.
    """

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("api_login")
        self.logout_url = reverse("api_logout")

        self.admin = User.objects.create_user(
            username="admin_rallye",
            password="Segura123!",
        )
        self.admin_inactivo = User.objects.create_user(
            username="admin_inactivo",
            password="Segura123!",
            is_active=False,
        )

    def _login(self, username="admin_rallye", password="Segura123!"):
        """Helper: hace login y retorna la response completa."""
        return self.client.post(
            self.url,
            {"username": username, "password": password},
            format="json",
        )

    def _get_tokens(self, username="admin_rallye", password="Segura123!"):
        """Helper: retorna (access, refresh) tras login exitoso."""
        response = self._login(username, password)
        return response.data["access"], response.data["refresh"]

    # ═══════════════════════════════════════════════════════════════════════
    # CA-01: El administrador puede ingresar sus credenciales
    # ═══════════════════════════════════════════════════════════════════════

    def test_cp01_login_exitoso_credenciales_correctas(self):
        """
        CP-01 · Flujo feliz
        Credenciales correctas → 200 + access + refresh + username.
        """
        response = self._login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["username"], "admin_rallye")

    def test_cp02_login_exitoso_retorna_jwt_valido(self):
        """
        CP-02 · El access token retornado tiene formato JWT (tres segmentos).
        """
        response = self._login()

        access = response.data["access"]
        partes = access.split(".")
        self.assertEqual(len(partes), 3, "El access token no tiene formato JWT válido.")

    def test_cp03_login_exitoso_retorna_refresh_valido(self):
        """
        CP-03 · El refresh token retornado tiene formato JWT (tres segmentos).
        """
        response = self._login()

        refresh = response.data["refresh"]
        partes = refresh.split(".")
        self.assertEqual(len(partes), 3, "El refresh token no tiene formato JWT válido.")

    def test_cp04_login_username_con_espacios_extremos(self):
        """
        CP-04 · Username con espacios al inicio y al final.
        El serializer hace strip() → debe autenticar correctamente.
        """
        response = self.client.post(
            self.url,
            {"username": "  admin_rallye  ", "password": "Segura123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cp05_login_password_case_sensitive(self):
        """
        CP-05 · Password es case-sensitive.
        'segura123!' ≠ 'Segura123!' → debe rechazar.
        """
        response = self._login(password="segura123!")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ═══════════════════════════════════════════════════════════════════════
    # CA-02: El sistema valida las credenciales ingresadas
    # ═══════════════════════════════════════════════════════════════════════

    def test_cp06_login_falla_password_incorrecto(self):
        """
        CP-06 · Password incorrecto → 400 con clave 'error'.
        """
        response = self._login(password="WrongPass999")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_cp07_login_falla_username_incorrecto(self):
        """
        CP-07 · Username que no existe → 400 con clave 'error'.
        """
        response = self._login(username="noexiste")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_cp08_login_falla_username_vacio(self):
        """
        CP-08 · Username vacío → 400.
        """
        response = self.client.post(
            self.url,
            {"username": "", "password": "Segura123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp09_login_falla_password_vacio(self):
        """
        CP-09 · Password vacío → 400.
        """
        response = self.client.post(
            self.url,
            {"username": "admin_rallye", "password": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp10_login_falla_ambos_campos_vacios(self):
        """
        CP-10 · Username y password vacíos → 400.
        """
        response = self.client.post(
            self.url,
            {"username": "", "password": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp11_login_falla_payload_vacio(self):
        """
        CP-11 · Payload completamente vacío {} → 400.
        """
        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp12_login_falla_sin_campo_username(self):
        """
        CP-12 · Payload sin campo username → 400.
        """
        response = self.client.post(
            self.url,
            {"password": "Segura123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp13_login_falla_sin_campo_password(self):
        """
        CP-13 · Payload sin campo password → 400.
        """
        response = self.client.post(
            self.url,
            {"username": "admin_rallye"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp14_login_falla_campos_solo_espacios(self):
        """
        CP-14 · Campos con solo espacios → 400.
        """
        response = self.client.post(
            self.url,
            {"username": "   ", "password": "   "},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp15_login_falla_username_demasiado_largo(self):
        """
        CP-15 · Username con más de 150 caracteres → 400.
        """
        username_largo = "a" * 151
        response = self.client.post(
            self.url,
            {"username": username_largo, "password": "Segura123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp16_login_falla_metodo_get_no_permitido(self):
        """
        CP-16 · GET a /api/users/login/ → 405 Method Not Allowed.
        """
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cp17_login_falla_metodo_put_no_permitido(self):
        """
        CP-17 · PUT a /api/users/login/ → 405 Method Not Allowed.
        """
        response = self.client.put(
            self.url,
            {"username": "admin_rallye", "password": "Segura123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cp18_login_falla_metodo_patch_no_permitido(self):
        """
        CP-18 · PATCH a /api/users/login/ → 405 Method Not Allowed.
        """
        response = self.client.patch(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cp19_login_falla_metodo_delete_no_permitido(self):
        """
        CP-19 · DELETE a /api/users/login/ → 405 Method Not Allowed.
        """
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cp20_login_respuesta_error_no_expone_detalles_internos(self):
        """
        CP-20 · Seguridad: el mensaje de error no revela si el username
        existe o no (mismo mensaje para credenciales incorrectas).
        """
        response_bad_pass = self._login(password="wrong")
        response_bad_user = self._login(username="noexiste")

        self.assertIn("error", response_bad_pass.data)
        self.assertIn("error", response_bad_user.data)
        self.assertEqual(
            response_bad_pass.data["error"],
            response_bad_user.data["error"],
        )

    # ═══════════════════════════════════════════════════════════════════════
    # CA-03: El acceso solo se permite a cuentas registradas
    # ═══════════════════════════════════════════════════════════════════════

    def test_cp21_login_falla_cuenta_inexistente(self):
        """
        CP-21 · Usuario no registrado en BD → 400.
        """
        response = self._login(username="intruso", password="cualquierpass")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_cp22_login_falla_cuenta_inactiva(self):
        """
        CP-22 · Cuenta desactivada → 400.
        """
        response = self._login(username="admin_inactivo")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_cp23_login_falla_superuser_inactivo(self):
        """
        CP-23 · Superuser con is_active=False → 400.
        """
        User.objects.create_superuser(
            username="super_inactivo",
            password="Segura123!",
            is_active=False,
        )
        response = self._login(username="super_inactivo")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp24_login_exitoso_superuser_activo(self):
        """
        CP-24 · Superuser activo puede iniciar sesión normalmente.
        """
        User.objects.create_superuser(
            username="super_activo",
            password="Segura123!",
        )
        response = self._login(username="super_activo")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    # ═══════════════════════════════════════════════════════════════════════
    # CA-04: Al iniciar sesión correctamente se accede al panel
    # ═══════════════════════════════════════════════════════════════════════

    def test_cp25_token_valido_permite_acceso_a_endpoint_protegido(self):
        """
        CP-25 · Access token válido → endpoint protegido responde 200.
        """
        access, refresh = self._get_tokens()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(
            self.logout_url,
            {"refresh": refresh},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cp26_acceso_sin_token_rechazado(self):
        """
        CP-26 · Sin token → endpoint protegido responde 401.
        """
        self.client.credentials()
        response = self.client.post(
            self.logout_url,
            {"refresh": "fake"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cp27_acceso_con_token_malformado_rechazado(self):
        """
        CP-27 · Token malformado (no es JWT) → 401.
        """
        self.client.credentials(HTTP_AUTHORIZATION="Bearer esto.no.es.un.jwt.valido")
        response = self.client.post(
            self.logout_url,
            {"refresh": "fake"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cp28_acceso_con_token_aleatorio_rechazado(self):
        """
        CP-28 · Token con estructura JWT pero contenido aleatorio → 401.
        """
        token_falso = (
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9"
            ".eyJmYWtlIjoidHJ1ZSJ9"
            ".invalidsig"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_falso}")
        response = self.client.post(
            self.logout_url,
            {"refresh": "fake"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cp29_acceso_con_refresh_como_access_rechazado(self):
        """
        CP-29 · Usar el refresh token como access token → 401.
        """
        _, refresh = self._get_tokens()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh}")
        response = self.client.post(
            self.logout_url,
            {"refresh": refresh},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cp30_login_multiple_sesiones_generan_tokens_distintos(self):
        """
        CP-30 · Dos logins seguidos generan tokens distintos cada vez.
        """
        response1 = self._login()
        response2 = self._login()

        self.assertNotEqual(response1.data["access"], response2.data["access"])
        self.assertNotEqual(response1.data["refresh"], response2.data["refresh"])

    # ═══════════════════════════════════════════════════════════════════════
    # Logout
    # ═══════════════════════════════════════════════════════════════════════

    def test_cp31_logout_exitoso_invalida_refresh_token(self):
        """
        CP-31 · Logout correcto → 200 + mensaje.
        """
        access, refresh = self._get_tokens()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(
            self.logout_url,
            {"refresh": refresh},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

    def test_cp32_logout_falla_sin_refresh_token(self):
        """
        CP-32 · Logout sin enviar refresh token → 400.
        """
        access, _ = self._get_tokens()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(self.logout_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp33_logout_falla_refresh_token_invalido(self):
        """
        CP-33 · Logout con refresh token malformado → 400.
        """
        access, _ = self._get_tokens()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.post(
            self.logout_url,
            {"refresh": "esto.no.es.valido"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp34_logout_falla_refresh_ya_en_blacklist(self):
        """
        CP-34 · Refresh token ya usado en logout anterior → 400.
        No se puede hacer logout dos veces con el mismo token.
        """
        access, refresh = self._get_tokens()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        self.client.post(self.logout_url, {"refresh": refresh}, format="json")
        response = self.client.post(
            self.logout_url,
            {"refresh": refresh},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp35_logout_falla_sin_access_token(self):
        """
        CP-35 · Logout sin Authorization header → 401.
        """
        _, refresh = self._get_tokens()

        self.client.credentials()
        response = self.client.post(
            self.logout_url,
            {"refresh": refresh},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cp36_logout_falla_metodo_get_no_permitido(self):
        """
        CP-36 · GET a /api/users/logout/ → 405.
        """
        access, _ = self._get_tokens()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cp37_refresh_blacklisted_lanza_token_error(self):
        """
        CP-37 · Tras logout, el refresh token queda en blacklist
        y lanza TokenError si se intenta usar directamente.
        """
        from rest_framework_simplejwt.exceptions import TokenError

        access, refresh = self._get_tokens()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        self.client.post(self.logout_url, {"refresh": refresh}, format="json")

        with self.assertRaises(TokenError):
            RefreshToken(refresh)

    def test_cp38_login_acepta_multipart_form(self):
        """
        CP-38 · La API acepta multipart/form-data (DRF lo soporta por defecto).
        """
        response = self.client.post(
            self.url,
            {"username": "admin_rallye", "password": "Segura123!"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cp39_login_campos_nulos_rechazados(self):
        """
        CP-39 · Campos con valor null → 400.
        """
        response = self.client.post(
            self.url,
            {"username": None, "password": None},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cp40_login_campos_numericos_no_autentican(self):
        """
        CP-40 · Valores numéricos en username/password → no debe devolver 200.
        DRF coerciona a string pero no existirá ese usuario.
        """
        response = self.client.post(
            self.url,
            {"username": 12345, "password": 99999},
            format="json",
        )

        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

    def test_cp41_dos_usuarios_tokens_no_se_mezclan(self):
        """
        CP-41 · El access de un admin no puede usarse para logout
        del refresh de otro admin sin que falle de forma controlada.
        """
        User.objects.create_user(username="otro_admin", password="Segura123!")

        access1, _ = self._get_tokens(username="admin_rallye")
        _, refresh2 = self._get_tokens(username="otro_admin")

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access1}")
        response = self.client.post(
            self.logout_url,
            {"refresh": refresh2},
            format="json",
        )

        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST],
        )

    def test_cp42_login_respuesta_contiene_exactamente_tres_claves(self):
        """
        CP-42 · La respuesta exitosa tiene exactamente: access, refresh, username.
        No debe filtrar información extra del usuario.
        """
        response = self._login()

        claves = set(response.data.keys())
        self.assertEqual(claves, {"access", "refresh", "username"})
