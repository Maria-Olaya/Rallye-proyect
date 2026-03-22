from django.contrib.auth import authenticate
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            "required": "El correo es obligatorio.",
            "blank": "El correo no puede estar vacío.",
        }
    )
    password = serializers.CharField(
        write_only=True,
        error_messages={
            "required": "La contraseña es obligatoria.",
            "blank": "La contraseña no puede estar vacía.",
        },
    )

    def validate(self, data):
        email = data.get("email", "").strip()
        password = data.get("password", "").strip()

        if not email or not password:
            raise serializers.ValidationError("Correo y contraseña son obligatorios.")

        user = authenticate(username=email, password=password)

        if user is None:
            raise serializers.ValidationError("Credenciales incorrectas.")

        if not user.is_active:
            raise serializers.ValidationError("Esta cuenta está desactivada.")

        if user.is_superuser:
            raise serializers.ValidationError("Los superusuarios no acceden por esta vía.")

        data["user"] = user
        return data
