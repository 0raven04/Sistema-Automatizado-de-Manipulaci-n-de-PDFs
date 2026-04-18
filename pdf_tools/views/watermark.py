from django.core.exceptions import ValidationError
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema

from ..services.memory import leer_subida
from ..services.pdf_operations import watermark_pdf
from .utils import _iterar_buffer


@method_decorator(
    ratelimit(key="ip", rate="10/m", block=True),
    name="post"
)
@extend_schema(
    request={
        "multipart/form-data": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "format": "binary"},
                "texto": {"type": "string", "example": "CONFIDENCIAL"},
                "opacidad": {"type": "number", "example": 0.3},
                "posicion": {"type": "string", "example": "center"},
            },
            "required": ["file", "texto"],
        }
    },
    responses={200: {"type": "string", "format": "binary"}, 400: dict, 429: dict},
    summary="Agregar marca de agua",
    description="Aplica una marca de agua de texto sobre todas las páginas del PDF.",
)
class WatermarkPDFView(View):
    def post(self, request):
        try:
            archivo = request.FILES.get("file")
            texto = request.POST.get("texto", "").strip()
            if not texto:
                raise ValidationError("Debes enviar el texto de la marca de agua en 'texto'.")
            raw_opacidad = request.POST.get("opacidad", "0.2")
            posicion = request.POST.get("posicion", "center")

            try:
                opacidad = float(raw_opacidad)
            except ValueError as exc:
                raise ValidationError("El campo 'opacidad' debe ser numérico.") from exc

            buffer = leer_subida(archivo)
            resultado = watermark_pdf(
                buffer,
                texto=texto,
                opacidad=opacidad,
                posicion=posicion,
            )

            response = StreamingHttpResponse(
                _iterar_buffer(resultado),
                content_type="application/pdf",
            )
            response["Content-Disposition"] = 'attachment; filename="watermark.pdf"'
            return response
        except ValidationError as exc:
            return JsonResponse({"error": exc.message}, status=400)
