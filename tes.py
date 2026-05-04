# fix_tests_make_local.py
# Ejecutar desde la RAÍZ del repo: python fix_tests_make_local.py

from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"

OK = "\033[92m✔\033[0m"
ERR = "\033[91m✘\033[0m"
INF = "\033[94m→\033[0m"

print(f"\n{INF} Corrigiendo tests.py …")

tests = BACKEND / "core" / "tests.py"
text = tests.read_text(encoding="utf-8")

OLD = (
    "    return Local.objects.create(\n"
    '        nombre="Local Centro",\n'
    "        sede=sede,\n"
    '        direccion="Cra 50",\n'
    '        telefono="3001234567",\n'
    '        correo_admin="local@test.com",\n'
    '        hora_apertura="08:00",\n'
    '        hora_cierre="18:00",\n'
    "        num_mecanicos=3,\n"
    "    )"
)

NEW = (
    "    return Local.objects.create(\n"
    '        nombre="Local Centro",\n'
    "        sede=sede,\n"
    '        direccion="Cra 50",\n'
    '        telefono="3001234567",\n'
    '        correo_admin="local@test.com",\n'
    "        num_mecanicos=3,\n"
    "    )"
)

if "".join(OLD) in text:
    tests.write_text(text.replace("".join(OLD), "".join(NEW), 1), encoding="utf-8")
    print(f"  {OK} hora_apertura/hora_cierre eliminados de make_local()")
else:
    print(
        f"  {ERR} Fragmento no encontrado — edita manualmente: quita hora_apertura y hora_cierre de make_local()"
    )

print(f"\n{OK} Ahora corre:")
print("  ruff check .")
print("  ruff format .")
print("  python manage.py test core")
print(
    "  git add -A && git commit -m 'feat(HU-16): horarios multiples por franja dias/apertura/cierre'"
)
print("  git push\n")
