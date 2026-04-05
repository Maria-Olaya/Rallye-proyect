# catalog/serializers.py

from datetime import date

from rest_framework import serializers

from catalog.models import Motocicleta


class MotocicletaSerializer(serializers.ModelSerializer):
    tipo = serializers.ChoiceField(
        choices=Motocicleta.TipoMotocicleta.choices,
        error_messages={"required": "El tipo de motocicleta es obligatorio."},
    )
    referencia = serializers.CharField(
        error_messages={
            "required": "La referencia es obligatoria.",
            "blank": "La referencia no puede estar vacía.",
        }
    )

    cilindraje = serializers.IntegerField(
        min_value=1,
        error_messages={
            "required": "El cilindraje es obligatorio.",
            "min_value": "El cilindraje debe ser mayor a 0.",
        },
    )
    anio = serializers.IntegerField(error_messages={"required": "El año es obligatorio."})
    precio = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={"required": "El precio es obligatorio."},
    )
    caracteristicas = serializers.CharField(
        error_messages={
            "required": "Las características son obligatorias.",
            "blank": "Las características no pueden estar vacías.",
        }
    )

    class Meta:
        model = Motocicleta
        fields = [
            "id",
            "marca",
            "referencia",
            "anio",
            "tipo",
            "cilindraje",
            "precio",
            "caracteristicas",
            "imagen",
            "activa",
        ]
        read_only_fields = ["id", "marca", "activa"]

    def validate_cilindraje(self, value):
        if value <= 0:
            raise serializers.ValidationError("El cilindraje debe ser mayor a 0.")
        return value

    def validate_anio(self, value):
        anio_actual = date.today().year
        if value < 1900 or value > anio_actual + 1:
            raise serializers.ValidationError(f"Ingrese un año válido entre 1900 y {anio_actual + 1}.")
        return value

    def validate_precio(self, value):
        if value < 0:
            raise serializers.ValidationError("El precio no puede ser negativo.")
        return value
