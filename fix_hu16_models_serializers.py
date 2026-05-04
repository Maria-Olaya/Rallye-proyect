# fix_serializer_only.py
# Ejecutar desde la RAÍZ del repo: python fix_serializer_only.py

from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"

OK = "\033[92m✔\033[0m"
ERR = "\033[91m✘\033[0m"
INF = "\033[94m→\033[0m"

print(f"\n{INF} Corrigiendo serializers.py …")

ser = BACKEND / "core" / "serializers.py"
text = ser.read_text(encoding="utf-8")

OLD = (
    '            "nombre",  # read-only, para mostrar en el formulario\n'
    '            "telefono",\n'
    '            "direccion",\n'
    '            "descripcion",\n'
    '            "horarios",\n'
    '            "correo_admin",\n'
    '            "num_mecanicos",\n'
    '            "activo",\n'
    '            "dias_atencion",\n'
    "        ]\n"
    '        read_only_fields = ["nombre"]'
)

NEW = (
    '            "nombre",  # read-only, para mostrar en el formulario\n'
    '            "telefono",\n'
    '            "direccion",\n'
    '            "descripcion",\n'
    '            "correo_admin",\n'
    '            "num_mecanicos",\n'
    '            "activo",\n'
    '            "horarios",\n'
    "        ]\n"
    '        read_only_fields = ["nombre"]'
)

if "".join(OLD) in text:
    ser.write_text(text.replace("".join(OLD), "".join(NEW), 1), encoding="utf-8")
    print(f"  {OK} dias_atencion eliminado, horarios al final")
else:
    print(
        f"  {ERR} Fragmento no encontrado — pegando el serializer completo directamente"
    )
    FULL = '''\
from rest_framework import serializers
from core.models import Sede, Local


class LocalSerializer(serializers.ModelSerializer):
    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True)

    class Meta:
        model = Local
        fields = [
            "id",
            "nombre",
            "sede_nombre",
            "direccion",
            "telefono",
            "horarios",
        ]


class SedeSerializer(serializers.ModelSerializer):
    locales = LocalSerializer(many=True, read_only=True)

    class Meta:
        model = Sede
        fields = ["id", "nombre", "locales"]


# hu 16 - CORREGIDO
class LocalUpdateSerializer(serializers.ModelSerializer):
    """Serializer para edicion de informacion del local (HU-16)."""

    nombre = serializers.CharField(read_only=True)

    class Meta:
        model = Local
        fields = [
            "nombre",
            "telefono",
            "direccion",
            "descripcion",
            "correo_admin",
            "num_mecanicos",
            "activo",
            "horarios",
        ]
        read_only_fields = ["nombre"]
'''
    ser.write_text(FULL, encoding="utf-8")
    print(f"  {OK} serializers.py reescrito completo")

print(f"\n{OK} Listo. Ahora corre:")
print("  cd backend && python manage.py migrate")
print("  ruff check . && ruff format .")
print("  python manage.py test core")
print("  git add -A && git commit -m 'feat(HU-16): horarios multiples por franja'")
print("  git push\n")
