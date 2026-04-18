from django.core.exceptions import ValidationError
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema

from ..services.memory import leer_subida
from ..services.pdf_operations import merge_pdfs
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
                "files": {
                    "type": "array",
                    "items": {"type": "string", "format": "binary"},
                }
            },
            "required": ["files"],
        }
    },
    responses={200: {"type": "string", "format": "binary"}, 400: dict, 429: dict},
    summary="Unir múltiples PDFs",
    description="Recibe dos o más archivos PDF en 'files' y devuelve un único PDF combinado.",
)

class MergePDFView(View):
    def post(self, request):
        try:
            archivos = request.FILES.getlist("files")
            if not archivos:
                raise ValidationError("Debes enviar archivos en el campo 'files'.")
            buffers = [leer_subida(archivo) for archivo in archivos]
            resultado = merge_pdfs(buffers)
            response = StreamingHttpResponse(
                _iterar_buffer(resultado),
                content_type="application/pdf",
            )
            response["Content-Disposition"] = 'attachment; filename="merge.pdf"'
            return response
        except ValidationError as exc:
            return JsonResponse({"error": exc.message}, status=400)
