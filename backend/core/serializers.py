# core/serializers.py
# NOTA: este archivo reemplaza/actualiza el existente.
# Si ya tienes campos adicionales en tu serializer actual, fusiónalos con estos cambios.

from rest_framework import serializers
from core.models import Local, Municipio, Sede


class MunicipioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipio
        fields = ["id", "nombre", "departamento"]


class LocalSerializer(serializers.ModelSerializer):
    """
    Serializer público de Local.
    Expone teléfono, descripción, horarios y los nuevos campos de servicios.
    """

    servicios = serializers.SerializerMethodField()

    class Meta:
        model = Local
        fields = [
            "id",
            "nombre",
            "direccion",
            "telefono",
            "descripcion",
            "horarios",
            "tiene_comercio",
            "tiene_taller",
            "servicios",       # lista legible para el popup
            "activo",
        ]

    def get_servicios(self, obj):
        """Devuelve una lista de strings con los servicios activos del local."""
        servicios = []
        if obj.tiene_comercio:
            servicios.append("Comercio (venta de motos y repuestos)")
        if obj.tiene_taller:
            servicios.append("Taller mecánico")
        return servicios


class SedeSerializer(serializers.ModelSerializer):
    """
    Serializer de Sede con locales anidados.
    Incluye municipio_nombre para compatibilidad con el template existente.
    """

    municipio_nombre = serializers.SerializerMethodField()
    locales = LocalSerializer(many=True, read_only=True)

    class Meta:
        model = Sede
        fields = [
            "id",
            "nombre",
            "direccion",
            "municipio_nombre",
            "lat",
            "lng",
            "activa",
            "locales",
        ]

    def get_municipio_nombre(self, obj):
        return str(obj.municipio) if obj.municipio_id else ""


class LocalUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para edición del local por su administrador (PATCH).
    Incluye los nuevos campos de servicios.
    """

    class Meta:
        model = Local
        fields = [
            "id",
            "nombre",
            "direccion",
            "telefono",
            "descripcion",
            "horarios",
            "tiene_comercio",
            "tiene_taller",
        ]
