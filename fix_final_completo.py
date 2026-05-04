# fix_final_completo.py
from pathlib import Path

ROOT    = Path(__file__).parent
BACKEND = ROOT / "backend"
mig_dir = BACKEND / "core" / "migrations"

OK  = "\033[92m✔\033[0m"
INF = "\033[94m→\033[0m"

# 1. Reescribir 0006 para eliminar hora_apertura, hora_cierre Y dias_atencion, y agregar horarios
print(f"\n{INF} Reescribiendo 0006_local_horarios.py …")
(mig_dir / "0006_local_horarios.py").write_text(
    """\
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_local_horarios"),
    ]

    operations = [
        migrations.RemoveField(model_name="local", name="hora_apertura"),
        migrations.RemoveField(model_name="local", name="hora_cierre"),
        migrations.RemoveField(model_name="local", name="dias_atencion"),
        migrations.AddField(
            model_name="local",
            name="horarios",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text=(
                    "Lista de franjas: "
                    '[{"dias":["lun","mar"], "apertura":"08:00", "cierre":"17:00"}]'
                ),
            ),
        ),
    ]
""",
    encoding="utf-8",
)
print(f"  {OK} 0006 reescrita: elimina hora_apertura, hora_cierre, dias_atencion + agrega horarios")

# 2. Reescribir tests.py completo y limpio
print(f"\n{INF} Reescribiendo tests.py …")
(BACKEND / "core" / "tests.py").write_text(
    """\
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
""",
    encoding="utf-8",
)
print(f"  {OK} tests.py reescrito limpio (sin hora_apertura/hora_cierre)")

print(f"\n{OK} Listo. Ahora corre:")
print("  python manage.py migrate core 0003 --fake")
print("  python manage.py migrate core")
print("  python manage.py test core")