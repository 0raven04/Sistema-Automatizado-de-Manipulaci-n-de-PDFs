from django.core.exceptions import ValidationError
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema

from ..services.memory import leer_subida
from ..services.pdf_operations import rotate_pdf
from .utils import _iterar_buffer


@method_decorator(
    ratelimit(key="ip", rate=settings.RATE_LIMIT, block=True),
    name="post"
)
@extend_schema(
    request={
        "multipart/form-data": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "format": "binary"},
                "angulo": {"type": "integer", "example": 90},
                "paginas": {"type": "string", "example": "1,2"},
            },
            "required": ["file", "angulo"],
        }
    },
    responses={200: {"type": "string", "format": "binary"}, 400: dict, 429: dict},
    summary="Rotar páginas de un PDF",
    description="Rota páginas específicas o todas con ángulos permitidos de 90, 180 o 270.",
)

class RotatePDFView(View):
    def post(self, request):
        try:
            archivo = request.FILES.get("file")
            raw_angulo = request.POST.get("angulo")
            if raw_angulo is None:
                raise ValidationError("Debes enviar el ángulo en el campo 'angulo'.")

            try:
                angulo = int(raw_angulo)
            except ValueError as exc:
                raise ValidationError("El campo 'angulo' debe ser un número entero.") from exc

            paginas = request.POST.get("paginas", "").strip()
            paginas = paginas if paginas else None
            buffer = leer_subida(archivo)
            resultado = rotate_pdf(buffer, angulo=angulo, paginas=paginas)

            response = StreamingHttpResponse(
                _iterar_buffer(resultado),
                content_type="application/pdf",
            )
            response["Content-Disposition"] = 'attachment; filename="rotate.pdf"'
            return response
        except ValidationError as exc:
            return JsonResponse({"error": exc.message}, status=400)
