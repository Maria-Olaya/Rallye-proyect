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
        return value.strip()

    def validate_placa_moto(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Este campo es obligatorio.")
        return value.strip().upper()

    def validate_referencia_moto(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Este campo es obligatorio.")
        return value.strip()

    def validate_anio_moto(self, value):
        if value is None:
            raise serializers.ValidationError("Este campo es obligatorio.")
        if value < 1900:
            raise serializers.ValidationError("Ingrese un año válido.")
        return value

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.estado = Cita.Estado.ASIGNADA
        instance.save()
        return instance