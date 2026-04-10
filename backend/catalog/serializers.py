# catalog/serializers.py

import os
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

    def to_internal_value(self, data):
        """Trunca el nombre del archivo ANTES de que DRF valide max_length del campo imagen."""
        imagen = data.get("imagen")
        if hasattr(imagen, "name") and len(imagen.name) > 100:
            extension = os.path.splitext(imagen.name)[1]  # ej. '.png'
            max_base = 99 - len(extension)
            imagen.name = imagen.name[:max_base] + extension  # resultado ≤ 100 chars
        return super().to_internal_value(data)

    def validate_imagen(self, value):
        """Valida tamaño máximo: 5 MB."""
        if value and hasattr(value, "size") and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("La imagen no puede superar los 5 MB.")
        return value

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


class MotocicletaEstadoSerializer(serializers.ModelSerializer):
    """Serializer de solo lectura para respuestas de cambio de estado — HU-15"""

    class Meta:
        model = Motocicleta
        fields = ["id", "marca", "referencia", "anio", "activa"]

class MotocicletaListSerializer(serializers.ModelSerializer):
    """Serializer de solo lectura para el catálogo público — HU-11"""

    imagen_url = serializers.SerializerMethodField()
    precio_display = serializers.SerializerMethodField()
    tipo_display = serializers.SerializerMethodField()

    class Meta:
        model = Motocicleta
        fields = [
            "id",
            "marca",
            "referencia",
            "anio",
            "tipo",
            "tipo_display",
            "cilindraje",
            "precio",
            "precio_display",
            "caracteristicas",
            "imagen_url",
            "activa",
        ]

    def get_imagen_url(self, obj):
        request = self.context.get("request")
        if obj.imagen and request:
            return request.build_absolute_uri(obj.imagen.url)
        return None

    def get_precio_display(self, obj):
        return f"$ {int(obj.precio):,}".replace(",", ".")

    def get_tipo_display(self, obj):
        return obj.get_tipo_display()
