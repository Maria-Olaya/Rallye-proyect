import re
from datetime import date

from rest_framework import serializers

from scheduling.models import Cita


class CitaDisponibleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cita
        fields = ["id", "fecha", "hora_inicio", "hora_fin"]


class AgendarCitaSerializer(serializers.ModelSerializer):
    tipo_servicio = serializers.ChoiceField(choices=Cita.TipoServicio.choices, required=True)
    tipo_documento = serializers.ChoiceField(choices=Cita.TipoDocumento.choices, required=True)
    cliente_nombre = serializers.CharField(required=True, allow_blank=False)
    cliente_documento = serializers.CharField(required=True, allow_blank=False)
    cliente_telefono = serializers.CharField(required=True, allow_blank=False)
    cliente_correo = serializers.EmailField(required=True, allow_blank=False)
    placa_moto = serializers.CharField(required=True, allow_blank=False)
    referencia_moto = serializers.CharField(required=True, allow_blank=False)
    anio_moto = serializers.IntegerField(required=True)

    class Meta:
        model = Cita
        fields = [
            "tipo_servicio",
            "tipo_documento",
            "cliente_nombre",
            "cliente_documento",
            "cliente_telefono",
            "cliente_correo",
            "placa_moto",
            "referencia_moto",
            "anio_moto",
        ]

    def validate(self, attrs):
        cita = self.instance

        if cita is None:
            raise serializers.ValidationError("Cita no encontrada.")

        if cita.estado != Cita.Estado.LIBRE:
            raise serializers.ValidationError("Esta cita ya no está disponible.")

        return attrs

    def validate_cliente_nombre(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Este campo es obligatorio.")
        return value.strip()

    def validate_cliente_documento(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Este campo es obligatorio.")
        return value.strip()

    def validate_cliente_telefono(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Este campo es obligatorio.")
        digitos = re.sub(r"\D", "", value)
        if len(digitos) < 7 or len(digitos) > 10:
            raise serializers.ValidationError("El teléfono debe tener entre 7 y 10 dígitos.")
        return digitos

    def validate_placa_moto(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Este campo es obligatorio.")
        placa = value.strip().upper()
        if not re.match(r"^[A-Z]{3}\d{2}[A-Z]$", placa):
            raise serializers.ValidationError("Formato de placa inválido. Ejemplo: AXA39C")
        return placa

    def validate_referencia_moto(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Este campo es obligatorio.")
        return value.strip()

    def validate_anio_moto(self, value):
        if value is None:
            raise serializers.ValidationError("Este campo es obligatorio.")
        anio_actual = date.today().year
        if value < 1900 or value > anio_actual:
            raise serializers.ValidationError(f"Ingrese un año válido entre 1900 y {anio_actual}.")
        return value

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.estado = Cita.Estado.ASIGNADA
        instance.save()
        return instance
