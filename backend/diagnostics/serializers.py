from rest_framework import serializers

from diagnostics.models import Diagnostico
from scheduling.models import Cita


class CitaAtendidaLookupSerializer(serializers.ModelSerializer):
    local_nombre = serializers.CharField(source="local.nombre", read_only=True)

    class Meta:
        model = Cita
        fields = [
            "id",
            "fecha",
            "hora_inicio",
            "hora_fin",
            "placa_moto",
            "cliente_nombre",
            "cliente_documento",
            "cliente_telefono",
            "cliente_correo",
            "referencia_moto",
            "anio_moto",
            "tipo_servicio",
            "local_nombre",
        ]


class DiagnosticoCreateSerializer(serializers.ModelSerializer):
    cita_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Diagnostico
        fields = [
            "cita_id",
            "descripcion",
            "radicado",
            "fecha_registro",
            "registrado_por",
            "correo_radicado_enviado",
            "fecha_envio_radicado",
        ]
        read_only_fields = [
            "radicado",
            "fecha_registro",
            "registrado_por",
            "correo_radicado_enviado",
            "fecha_envio_radicado",
        ]

    def validate_descripcion(self, value):
        descripcion = value.strip()
        if len(descripcion) < 10:
            raise serializers.ValidationError("La descripción debe tener al menos 10 caracteres.")
        return descripcion

    def validate_cita_id(self, value):
        request = self.context["request"]
        try:
            cita = Cita.objects.select_related("local").get(pk=value)
        except Cita.DoesNotExist as exc:
            raise serializers.ValidationError("La cita seleccionada no existe.") from exc

        if request.user.local_id and cita.local_id != request.user.local_id:
            raise serializers.ValidationError("La cita no pertenece a tu local.")

        if cita.estado != Cita.Estado.ATENDIDO:
            raise serializers.ValidationError("Solo se puede registrar diagnóstico para citas en estado ATENDIDO.")

        if hasattr(cita, "diagnostico"):
            raise serializers.ValidationError("Esta cita ya tiene un diagnóstico registrado.")

        self.context["cita"] = cita
        return value

    def create(self, validated_data):
        cita = self.context["cita"]
        validated_data.pop("cita_id")
        return Diagnostico.objects.create(
            cita=cita,
            registrado_por=self.context["request"].user,
            **validated_data,
        )
