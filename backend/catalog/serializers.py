# catalog/serializers.py

import os
from datetime import date

from rest_framework import serializers

from catalog.models import CotizacionMotocicleta, Motocicleta
from core.models import Local


class MotocicletaSerializer(serializers.ModelSerializer):
    tipo = serializers.ChoiceField(
        choices=Motocicleta.TipoMotocicleta.choices,
        error_messages={"required": "El tipo de motocicleta es obligatorio."},
    )
    referencia = serializers.CharField(
        error_messages={
            "required": "La referencia es obligatoria.",
            "blank": "La referencia no puede estar vacia.",
        }
    )
    cilindraje = serializers.IntegerField(
        min_value=1,
        error_messages={
            "required": "El cilindraje es obligatorio.",
            "min_value": "El cilindraje debe ser mayor a 0.",
        },
    )
    anio = serializers.IntegerField(error_messages={"required": "El anio es obligatorio."})
    precio = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        error_messages={"required": "El precio es obligatorio."},
    )
    caracteristicas = serializers.CharField(
        error_messages={
            "required": "Las caracteristicas son obligatorias.",
            "blank": "Las caracteristicas no pueden estar vacias.",
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
        imagen = data.get("imagen")
        if hasattr(imagen, "name") and len(imagen.name) > 100:
            extension = os.path.splitext(imagen.name)[1]
            max_base = 99 - len(extension)
            imagen.name = imagen.name[:max_base] + extension
        return super().to_internal_value(data)

    def validate_imagen(self, value):
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
            raise serializers.ValidationError(f"Ingrese un anio valido entre 1900 y {anio_actual + 1}.")
        return value

    def validate_precio(self, value):
        if value < 0:
            raise serializers.ValidationError("El precio no puede ser negativo.")
        return value


class MotocicletaEstadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Motocicleta
        fields = ["id", "marca", "referencia", "anio", "activa"]


class MotocicletaListSerializer(serializers.ModelSerializer):
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


class CotizarMotocicletaSerializer(serializers.Serializer):
    motocicleta_id = serializers.IntegerField(error_messages={"required": "La motocicleta es obligatoria."})
    local_id = serializers.IntegerField(required=False, allow_null=True)
    cliente_nombre = serializers.CharField(required=False, allow_blank=True, max_length=120)
    cliente_correo = serializers.EmailField(required=False, allow_blank=True)
    cliente_telefono = serializers.CharField(required=False, allow_blank=True, max_length=20)
    comentario = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_motocicleta_id(self, value):
        try:
            motocicleta = Motocicleta.objects.get(pk=value, activa=True)
        except Motocicleta.DoesNotExist as exc:
            raise serializers.ValidationError("La motocicleta seleccionada no existe o no esta disponible.") from exc

        if motocicleta.precio <= 0:
            raise serializers.ValidationError("La motocicleta seleccionada no tiene un precio valido para cotizar.")

        self.context["motocicleta"] = motocicleta
        return value

    def validate_local_id(self, value):
        if value in (None, ""):
            self.context["local"] = None
            return None

        try:
            local = Local.objects.get(pk=value, activo=True)
        except Local.DoesNotExist as exc:
            raise serializers.ValidationError("El local seleccionado no existe o no esta disponible.") from exc

        self.context["local"] = local
        return value

    def validate_cliente_nombre(self, value):
        return value.strip()

    def validate_cliente_telefono(self, value):
        return value.strip()

    def validate_comentario(self, value):
        return value.strip()


class CotizacionMotocicletaResponseSerializer(serializers.ModelSerializer):
    motocicleta = serializers.SerializerMethodField()
    local = serializers.SerializerMethodField()
    whatsapp_url = serializers.CharField(read_only=True)

    class Meta:
        model = CotizacionMotocicleta
        fields = [
            "id",
            "radicado",
            "motocicleta",
            "local",
            "precio_base",
            "impuestos_estimados",
            "tramites_estimados",
            "total_estimado",
            "cliente_nombre",
            "cliente_correo",
            "cliente_telefono",
            "comentario",
            "correo_cotizacion_enviado",
            "fecha_envio_cotizacion",
            "whatsapp_url",
            "created_at",
        ]

    def get_motocicleta(self, obj):
        return {
            "id": obj.motocicleta_id,
            "marca": obj.motocicleta.marca,
            "referencia": obj.motocicleta.referencia,
            "anio": obj.motocicleta.anio,
            "tipo": obj.motocicleta.tipo,
            "cilindraje": obj.motocicleta.cilindraje,
        }

    def get_local(self, obj):
        if obj.local is None:
            return None
        return {
            "id": obj.local_id,
            "nombre": obj.local.nombre,
            "direccion": obj.local.direccion,
            "telefono": obj.local.telefono,
        }
