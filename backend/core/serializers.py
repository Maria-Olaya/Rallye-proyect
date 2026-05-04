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
            "hora_apertura",
            "hora_cierre",
        ]


class SedeSerializer(serializers.ModelSerializer):
    locales = LocalSerializer(many=True, read_only=True)

    class Meta:
        model = Sede
        fields = ["id", "nombre", "locales"]


# hu 16 — CORREGIDO: se amplían los fields para que GET devuelva todo
# lo que el template necesita (nombre, correo_admin, num_mecanicos, activo)
# y PATCH pueda actualizar los campos editables.

class LocalUpdateSerializer(serializers.ModelSerializer):
    """Serializer para edición de información del local (HU-16)."""

    # read-only: se devuelven en GET pero el PATCH los ignora
    nombre = serializers.CharField(read_only=True)

    class Meta:
        model = Local
        fields = [
            "nombre",           # read-only, para mostrar en el formulario
            "telefono",
            "direccion",
            "descripcion",
            "hora_apertura",
            "hora_cierre",
            "correo_admin",
            "num_mecanicos",
            "activo",
        ]
        read_only_fields = ["nombre"]
