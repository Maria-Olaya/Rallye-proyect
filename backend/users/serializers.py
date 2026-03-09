from django.contrib.auth import authenticate
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        error_messages={"required": "El usuario es obligatorio.", "blank": "El usuario no puede estar vacío."},
    )
    password = serializers.CharField(
        write_only=True,
        error_messages={"required": "La contraseña es obligatoria.", "blank": "La contraseña no puede estar vacía."},
    )

    def validate(self, data):
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            raise serializers.ValidationError("Usuario y contraseña son obligatorios.")

        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError("Credenciales incorrectas.")

        if not user.is_active:
            raise serializers.ValidationError("Esta cuenta está desactivada.")

        data["user"] = user
        return data
