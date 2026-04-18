import json

from django.core.exceptions import ValidationError
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from .utils import _iterar_buffer
from ..services.pdf_operations import generate_pdf

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.conf import settings
from drf_spectacular.utils import extend_schema


@method_decorator(
    ratelimit(key="ip", rate=settings.RATE_LIMIT, block=True),
    name="post"
)
@extend_schema(
    request={"application/json": {"type": "object"}},
    responses={200: {"type": "string", "format": "binary"}, 400: dict, 429: dict},
    summary="Generar PDF desde JSON",
    description="Construye un PDF a partir de un payload JSON con título y secciones.",
)

class GeneratePDFView(View):
    def post(self, request):
        try:
            try:
                payload = json.loads(request.body.decode("utf-8") or "{}")
            except json.JSONDecodeError as exc:
                raise ValidationError("El cuerpo debe ser JSON válido.") from exc

            resultado = generate_pdf(payload)
            response = StreamingHttpResponse(
                _iterar_buffer(resultado),
                content_type="application/pdf",
            )
            response["Content-Disposition"] = 'attachment; filename="generate.pdf"'
            return response
        except ValidationError as exc:
            return JsonResponse({"error": exc.message}, status=400)
