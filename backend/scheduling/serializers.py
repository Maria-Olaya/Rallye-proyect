from rest_framework import serializers
from scheduling.models import Cita


class CitaDisponibleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cita
        fields = ["id", "fecha", "hora_inicio", "hora_fin"]


class AgendarCitaSerializer(serializers.ModelSerializer):
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

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.estado = Cita.Estado.ASIGNADA
        instance.save()
        return instance