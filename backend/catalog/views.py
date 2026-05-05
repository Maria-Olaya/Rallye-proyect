# catalog/views.py

import urllib.parse
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import ConsultaRepuesto, CotizacionMotocicleta, Motocicleta
from catalog.serializers import (
    CotizacionMotocicletaResponseSerializer,
    CotizarMotocicletaSerializer,
    MotocicletaEstadoSerializer,
    MotocicletaListSerializer,
    MotocicletaSerializer,
)
from catalog.services import (
    calcular_desglose_cotizacion,
    construir_enlace_whatsapp,
    enviar_cotizacion_por_correo,
    generar_radicado_cotizacion,
)
from core.models import Local


class AgregarMotocicletaView(APIView):
    """POST /api/catalog/motocicletas/agregar/ - HU-13"""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        serializer = MotocicletaSerializer(data=request.data)
        if serializer.is_valid():
            motocicleta = serializer.save(activa=True)
            return Response(
                {
                    "mensaje": "Motocicleta agregada al catalogo correctamente.",
                    "id": motocicleta.id,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CotizarMotocicletaView(APIView):
    """POST /api/catalog/cotizaciones/motocicletas/ - HU-10"""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CotizarMotocicletaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        motocicleta = serializer.context["motocicleta"]
        local = serializer.context.get("local")
        desglose = calcular_desglose_cotizacion(motocicleta.precio)
        radicado = generar_radicado_cotizacion()

        cotizacion = CotizacionMotocicleta.objects.create(
            usuario=request.user if request.user.is_authenticated else None,
            motocicleta=motocicleta,
            local=local,
            radicado=radicado,
            precio_base=desglose["precio_base"],
            impuestos_estimados=desglose["impuestos_estimados"],
            tramites_estimados=desglose["tramites_estimados"],
            total_estimado=desglose["total_estimado"],
            cliente_nombre=serializer.validated_data.get("cliente_nombre", ""),
            cliente_correo=serializer.validated_data.get("cliente_correo", ""),
            cliente_telefono=serializer.validated_data.get("cliente_telefono", ""),
            comentario=serializer.validated_data.get("comentario", ""),
        )

        correo_enviado = enviar_cotizacion_por_correo(cotizacion)
        whatsapp_url = construir_enlace_whatsapp(
            local.telefono if local else "",
            cotizacion.radicado,
            f"{motocicleta.marca} {motocicleta.referencia} {motocicleta.anio}",
            cotizacion.total_estimado,
        )

        response_data = CotizacionMotocicletaResponseSerializer(cotizacion).data
        response_data["whatsapp_url"] = whatsapp_url
        response_data["correo_cotizacion_enviado"] = correo_enviado
        return Response(response_data, status=status.HTTP_201_CREATED)


class EditarMotocicletaView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def _get_motocicleta(self, pk):
        try:
            return Motocicleta.objects.get(pk=pk)
        except Motocicleta.DoesNotExist:
            return None

    def get(self, request, pk):
        moto = self._get_motocicleta(pk)
        if moto is None:
            return Response(
                {"error": "Motocicleta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = MotocicletaSerializer(moto, context={"request": request})
        data = dict(serializer.data)
        if moto.imagen:
            data["imagen"] = request.build_absolute_uri(moto.imagen.url)
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        moto = self._get_motocicleta(pk)
        if moto is None:
            return Response(
                {"error": "Motocicleta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        tiene_imagen_nueva = "imagen" in request.FILES
        serializer = MotocicletaSerializer(
            moto,
            data=request.data,
            partial=not tiene_imagen_nueva,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "mensaje": "Motocicleta actualizada correctamente.",
                    "motocicleta": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        moto = self._get_motocicleta(pk)
        if moto is None:
            return Response(
                {"error": "Motocicleta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = MotocicletaSerializer(
            moto,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "mensaje": "Motocicleta actualizada correctamente.",
                    "motocicleta": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CatalogoMotocicletasView(APIView):
    """GET /api/catalog/motocicletas/ - HU-11 + HU-12"""

    permission_classes = [AllowAny]

    def get(self, request):
        motos = Motocicleta.objects.filter(activa=True).order_by("id")

        referencia = request.query_params.get("referencia", "").strip()
        tipo = request.query_params.get("tipo", "").strip().upper()
        cilindraje_min = request.query_params.get("cilindraje_min", "").strip()
        cilindraje_max = request.query_params.get("cilindraje_max", "").strip()

        if referencia:
            motos = motos.filter(referencia__icontains=referencia)

        if tipo:
            tipos_validos = [opcion[0] for opcion in Motocicleta.TipoMotocicleta.choices]
            if tipo not in tipos_validos:
                return Response([], status=status.HTTP_200_OK)
            motos = motos.filter(tipo=tipo)

        if cilindraje_min.isdigit():
            motos = motos.filter(cilindraje__gte=int(cilindraje_min))

        if cilindraje_max.isdigit():
            motos = motos.filter(cilindraje__lte=int(cilindraje_max))

        serializer = MotocicletaListSerializer(motos, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class DesactivarMotocicletaView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_motocicleta(self, pk):
        try:
            return Motocicleta.objects.get(pk=pk)
        except Motocicleta.DoesNotExist:
            return None

    def patch(self, request, pk):
        moto = self._get_motocicleta(pk)
        if moto is None:
            return Response(
                {"error": "Motocicleta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not moto.activa:
            return Response(
                {"error": "La motocicleta ya se encuentra inactiva."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        moto.activa = False
        moto.save(update_fields=["activa"])
        serializer = MotocicletaEstadoSerializer(moto)
        return Response(
            {
                "mensaje": "Motocicleta desactivada correctamente.",
                "motocicleta": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ActivarMotocicletaView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_motocicleta(self, pk):
        try:
            return Motocicleta.objects.get(pk=pk)
        except Motocicleta.DoesNotExist:
            return None

    def patch(self, request, pk):
        moto = self._get_motocicleta(pk)
        if moto is None:
            return Response(
                {"error": "Motocicleta no encontrada."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if moto.activa:
            return Response(
                {"error": "La motocicleta ya se encuentra activa."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        moto.activa = True
        moto.save(update_fields=["activa"])
        serializer = MotocicletaEstadoSerializer(moto)
        return Response(
            {
                "mensaje": "Motocicleta activada correctamente.",
                "motocicleta": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class ListadoAdminMotocicletasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        motos = Motocicleta.objects.all().order_by("id")
        serializer = MotocicletaListSerializer(motos, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ResumenComercialCotizacionesView(APIView):
    """
    GET /api/catalog/resumen-comercial/
    HU-20 — Resumen comercial interno basado únicamente en cotizaciones de motocicletas.

    Regla de local:
    1. Primero intenta usar request.user.local, si existe.
    2. Si el usuario no tiene local directo, busca un Local activo cuyo correo_admin
       coincida con el email del administrador autenticado.
    """

    permission_classes = [IsAuthenticated]

    @staticmethod
    def _decimal_to_float(value):
        if value is None:
            return 0
        if isinstance(value, Decimal):
            return float(value)
        return value

    @staticmethod
    def _parse_fecha(valor, nombre_campo):
        if not valor:
            return None, None
        try:
            return datetime.strptime(valor, "%Y-%m-%d").date(), None
        except ValueError:
            return None, f"{nombre_campo} debe tener formato YYYY-MM-DD."

    @staticmethod
    def _obtener_local_administrador(user):
        """
        Obtiene el local asociado al administrador autenticado.

        Primero intenta usar una relación directa user.local.
        Si esa relación no existe o está vacía, busca el local activo cuyo
        correo_admin sea igual al email del usuario autenticado.
        """
        local = None

        try:
            local = getattr(user, "local", None)
        except ObjectDoesNotExist:
            local = None

        if local is not None:
            return local

        email = (getattr(user, "email", "") or "").strip()

        if not email:
            return None

        return (
            Local.objects.select_related("sede").filter(correo_admin__iexact=email, activo=True).order_by("id").first()
        )

    @staticmethod
    def _respuesta_sin_local():
        return Response(
            {
                "mensaje": (
                    "No se encontró un local asociado al administrador autenticado. "
                    "Verifica que el correo del usuario coincida con el correo_admin de un local activo."
                ),
                "local": None,
                "periodo": None,
                "metricas": {
                    "total_cotizaciones": 0,
                    "valor_total_estimado": 0,
                    "promedio_cotizacion": 0,
                    "correos_enviados": 0,
                },
                "por_fecha": [],
                "por_tipo": [],
                "motos_mas_cotizadas": [],
                "cotizaciones_recientes": [],
            },
            status=status.HTTP_200_OK,
        )

    def get(self, request):
        local = self._obtener_local_administrador(request.user)

        if local is None:
            return self._respuesta_sin_local()

        fecha_inicio_txt = request.query_params.get("fecha_inicio", "").strip()
        fecha_fin_txt = request.query_params.get("fecha_fin", "").strip()

        hoy = timezone.localdate()
        fecha_inicio, error_inicio = self._parse_fecha(fecha_inicio_txt, "fecha_inicio")
        fecha_fin, error_fin = self._parse_fecha(fecha_fin_txt, "fecha_fin")

        if error_inicio:
            return Response({"fecha_inicio": error_inicio}, status=status.HTTP_400_BAD_REQUEST)
        if error_fin:
            return Response({"fecha_fin": error_fin}, status=status.HTTP_400_BAD_REQUEST)

        if fecha_inicio is None and fecha_fin is None:
            fecha_inicio = hoy.replace(day=1)
            fecha_fin = hoy
        elif fecha_inicio is None:
            fecha_inicio = fecha_fin.replace(day=1)
        elif fecha_fin is None:
            fecha_fin = hoy

        if fecha_inicio > fecha_fin:
            return Response(
                {"periodo": "La fecha de inicio no puede ser mayor que la fecha fin."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cotizaciones = (
            CotizacionMotocicleta.objects.select_related("motocicleta", "local", "local__sede")
            .filter(local=local)
            .filter(created_at__date__gte=fecha_inicio, created_at__date__lte=fecha_fin)
        )

        agregados = cotizaciones.aggregate(
            total_cotizaciones=Count("id"),
            valor_total_estimado=Sum("total_estimado"),
            promedio_cotizacion=Avg("total_estimado"),
            correos_enviados=Count("id", filter=Q(correo_cotizacion_enviado=True)),
        )

        por_fecha_queryset = (
            cotizaciones.annotate(fecha=TruncDate("created_at"))
            .values("fecha")
            .annotate(cantidad=Count("id"), valor_total=Sum("total_estimado"))
            .order_by("fecha")
        )

        datos_por_fecha = {
            item["fecha"]: {
                "cantidad": item["cantidad"],
                "valor_total": self._decimal_to_float(item["valor_total"]),
            }
            for item in por_fecha_queryset
        }

        por_fecha = []
        total_dias = (fecha_fin - fecha_inicio).days

        if total_dias <= 92:
            fecha_actual = fecha_inicio
            while fecha_actual <= fecha_fin:
                datos = datos_por_fecha.get(fecha_actual, {"cantidad": 0, "valor_total": 0})
                por_fecha.append(
                    {
                        "fecha": fecha_actual.isoformat(),
                        "cantidad": datos["cantidad"],
                        "valor_total": datos["valor_total"],
                    }
                )
                fecha_actual += timedelta(days=1)
        else:
            por_fecha = [
                {
                    "fecha": item["fecha"].isoformat(),
                    "cantidad": item["cantidad"],
                    "valor_total": self._decimal_to_float(item["valor_total"]),
                }
                for item in por_fecha_queryset
            ]

        tipos_display = dict(Motocicleta.TipoMotocicleta.choices)

        por_tipo = [
            {
                "tipo": item["motocicleta__tipo"] or "SIN_TIPO",
                "tipo_display": tipos_display.get(item["motocicleta__tipo"], "Sin tipo"),
                "cantidad": item["cantidad"],
                "valor_total": self._decimal_to_float(item["valor_total"]),
            }
            for item in cotizaciones.values("motocicleta__tipo")
            .annotate(cantidad=Count("id"), valor_total=Sum("total_estimado"))
            .order_by("-cantidad", "motocicleta__tipo")
        ]

        motos_mas_cotizadas = [
            {
                "motocicleta": (
                    f"{item['motocicleta__marca']} {item['motocicleta__referencia']} {item['motocicleta__anio']}"
                ),
                "cantidad": item["cantidad"],
                "valor_total": self._decimal_to_float(item["valor_total"]),
            }
            for item in cotizaciones.values(
                "motocicleta__marca",
                "motocicleta__referencia",
                "motocicleta__anio",
            )
            .annotate(cantidad=Count("id"), valor_total=Sum("total_estimado"))
            .order_by("-cantidad", "motocicleta__referencia")[:5]
        ]

        cotizaciones_recientes = []

        for cotizacion in cotizaciones.order_by("-created_at")[:8]:
            cotizaciones_recientes.append(
                {
                    "radicado": cotizacion.radicado or "Sin radicado",
                    "motocicleta": (
                        f"{cotizacion.motocicleta.marca} "
                        f"{cotizacion.motocicleta.referencia} "
                        f"{cotizacion.motocicleta.anio}"
                    ),
                    "cliente": cotizacion.cliente_nombre or "Cliente no registrado",
                    "fecha": timezone.localtime(cotizacion.created_at).strftime("%d/%m/%Y %H:%M"),
                    "total_estimado": self._decimal_to_float(cotizacion.total_estimado),
                    "correo_enviado": cotizacion.correo_cotizacion_enviado,
                }
            )

        return Response(
            {
                "local": {
                    "id": local.id,
                    "nombre": local.nombre,
                    "sede": local.sede.nombre if local.sede_id else None,
                    "direccion": local.direccion,
                    "correo_admin": local.correo_admin,
                },
                "periodo": {
                    "fecha_inicio": fecha_inicio.isoformat(),
                    "fecha_fin": fecha_fin.isoformat(),
                },
                "metricas": {
                    "total_cotizaciones": agregados["total_cotizaciones"] or 0,
                    "valor_total_estimado": self._decimal_to_float(agregados["valor_total_estimado"]),
                    "promedio_cotizacion": self._decimal_to_float(agregados["promedio_cotizacion"]),
                    "correos_enviados": agregados["correos_enviados"] or 0,
                },
                "por_fecha": por_fecha,
                "por_tipo": por_tipo,
                "motos_mas_cotizadas": motos_mas_cotizadas,
                "cotizaciones_recientes": cotizaciones_recientes,
            },
            status=status.HTTP_200_OK,
        )


# ── HU: Consultar repuestos guiado + Registrar interés ───────────────────────


class ModelosMotoView(APIView):
    """
    GET /api/catalog/repuestos/modelos/
    Paso 1 — devuelve referencias únicas de motos activas.
    Público.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        referencias = (
            Motocicleta.objects.filter(activa=True)
            .values_list("referencia", flat=True)
            .distinct()
            .order_by("referencia")
        )
        return Response({"modelos": list(referencias)}, status=status.HTTP_200_OK)


class AniosModeloView(APIView):
    """
    GET /api/catalog/repuestos/modelos/<referencia>/anios/
    Paso 2 — devuelve años disponibles para un modelo dado.
    Público.
    """

    permission_classes = [AllowAny]

    def get(self, request, referencia):
        anios = (
            Motocicleta.objects.filter(activa=True, referencia__iexact=referencia)
            .values_list("anio", flat=True)
            .distinct()
            .order_by("-anio")
        )
        if not anios.exists():
            return Response(
                {"error": "Modelo no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"modelo": referencia, "anios": list(anios)},
            status=status.HTTP_200_OK,
        )


class RegistrarConsultaRepuestoView(APIView):
    """
    POST /api/catalog/repuestos/consulta/
    Paso 3 — registra la consulta en tabla estadística y devuelve URL WhatsApp.
    Público.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        repuesto_nombre = request.data.get("repuesto_nombre", "").strip()
        if not repuesto_nombre:
            return Response(
                {"repuesto_nombre": "Este campo es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        repuesto_referencia = request.data.get("repuesto_referencia", "").strip()
        modelo_moto = request.data.get("modelo_moto", "").strip()
        local_id = request.data.get("local")

        local = None
        if local_id:
            try:
                local = Local.objects.select_related("sede").get(pk=local_id)
            except Local.DoesNotExist:
                return Response(
                    {"local": "El local seleccionado no existe."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        consulta = ConsultaRepuesto.objects.create(
            repuesto_nombre=repuesto_nombre,
            repuesto_referencia=repuesto_referencia,
            modelo_moto=modelo_moto,
            local=local,
        )

        whatsapp_url = None
        local_info = None

        if local:
            telefono = local.telefono.strip().replace(" ", "").replace("-", "")
            if telefono.startswith("+"):
                telefono = telefono[1:]
            if not telefono.startswith("57"):
                telefono = f"57{telefono}"

            mensaje = f"Hola, estoy interesado/a en el repuesto: *{consulta.repuesto_nombre}*"
            if consulta.repuesto_referencia:
                mensaje += f" (Ref: {consulta.repuesto_referencia})"
            if consulta.modelo_moto:
                mensaje += f". Es para una *{consulta.modelo_moto}*"
            mensaje += ". ¿Pueden ayudarme con disponibilidad y precio? Gracias."

            whatsapp_url = f"https://wa.me/{telefono}?text={urllib.parse.quote(mensaje)}"
            local_info = {
                "id": local.id,
                "nombre": local.nombre,
                "direccion": local.direccion,
                "telefono": local.telefono,
                "sede": local.sede.nombre,
            }

        return Response(
            {
                "mensaje": "Consulta registrada correctamente.",
                "consulta_id": consulta.id,
                "whatsapp_url": whatsapp_url,
                "local": local_info,
            },
            status=status.HTTP_201_CREATED,
        )
