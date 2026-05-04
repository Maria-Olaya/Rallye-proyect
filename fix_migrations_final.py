# fix_migrations_final.py
from pathlib import Path

ROOT    = Path(__file__).parent
BACKEND = ROOT / "backend"
mig_dir = BACKEND / "core" / "migrations"

OK  = "\033[92m✔\033[0m"
INF = "\033[94m→\033[0m"

# 1. Reescribir 0004 con default en dias_atencion para que no sea NOT NULL en tests
print(f"\n{INF} Reescribiendo 0004_local_dias_atencion.py …")
(mig_dir / "0004_local_dias_atencion.py").write_text(
    """\
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_alter_local_id_alter_municipio_id_alter_sede_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="local",
            name="dias_atencion",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
""",
    encoding="utf-8",
)
print(f"  {OK} 0004 reescrita con default=list (no NOT NULL)")

# 2. Reescribir 0005 (si existe) como no-op para evitar conflictos
print(f"\n{INF} Reescribiendo 0005_local_horarios.py como no-op …")
(mig_dir / "0005_local_horarios.py").write_text(
    """\
from django.db import migrations


class Migration(migrations.Migration):
    \"\"\"Migración vacía — placeholder para mantener el orden de dependencias.\"\"\"

    dependencies = [
        ("core", "0004_local_dias_atencion"),
    ]

    operations = []
""",
    encoding="utf-8",
)
print(f"  {OK} 0005 reescrita como no-op")

# 3. Reescribir 0006 para que elimine dias_atencion y agregue horarios
print(f"\n{INF} Reescribiendo 0006_local_horarios.py …")
(mig_dir / "0006_local_horarios.py").write_text(
    """\
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_local_horarios"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="local",
            name="dias_atencion",
        ),
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
print(f"  {OK} 0006 reescrita: RemoveField(dias_atencion) + AddField(horarios)")

print(f"\n{OK} Listo. Ahora corre:")
print("  python manage.py migrate core 0003 --fake-initial")
print("  python manage.py migrate core")
print("  python manage.py test core")