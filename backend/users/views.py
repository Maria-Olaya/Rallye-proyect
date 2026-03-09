from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from users.serializers import LoginSerializer


class LoginView(APIView):
    """
    POST /api/users/login/

    Recibe username y password, valida credenciales y retorna
    access token (JWT) y refresh token.

    Respuesta exitosa (200):
        {
            "access": "<jwt_access_token>",
            "refresh": "<jwt_refresh_token>",
            "username": "<username>"
        }

    Respuesta fallida (400):
        {
            "error": "<mensaje de error>"
        }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            errors = serializer.errors
            # Extraer el primer mensaje de error legible
            error_msg = ""
            for field_errors in errors.values():
                if isinstance(field_errors, list) and field_errors:
                    error_msg = field_errors[0]
                    break
            return Response({"error": str(error_msg)}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "username": user.username,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    POST /api/users/logout/

    Recibe el refresh token y lo invalida (blacklist).
    Requiere Authorization: Bearer <access_token> en el header.

    Respuesta exitosa (200):
        { "message": "Sesión cerrada correctamente." }

    Respuesta fallida (400):
        { "error": "Token inválido o ya expirado." }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({"error": "Se requiere el refresh token."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Sesión cerrada correctamente."}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Token inválido o ya expirado."}, status=status.HTTP_400_BAD_REQUEST)
