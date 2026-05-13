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
    municipio_nombre = serializers.CharField(source="municipio.nombre", read_only=True)

    class Meta:
        model = Sede
        fields = ["id", "nombre", "municipio_nombre", "direccion", "lat", "lng", "locales"]


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
