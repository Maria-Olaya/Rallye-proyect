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