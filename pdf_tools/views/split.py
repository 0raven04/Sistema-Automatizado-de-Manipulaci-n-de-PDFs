from django.core.exceptions import ValidationError
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema

from ..services.memory import leer_subida
from ..services.pdf_operations import split_pdf
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
                "paginas": {"type": "string", "example": "1,3-5"},
            },
            "required": ["file"],
        }
    },
    responses={200: {"type": "string", "format": "binary"}, 400: dict, 429: dict},
    summary="Extraer páginas de un PDF",
    description="Divide un PDF según la selección de páginas y devuelve un nuevo archivo.",
)

class SplitPDFView(View):
    def post(self, request):
        try:
            archivo = request.FILES.get("file")
            paginas = request.POST.get("paginas", "")
            buffer = leer_subida(archivo)
            resultado = split_pdf(buffer, paginas)

            response = StreamingHttpResponse(
                _iterar_buffer(resultado),
                content_type="application/pdf",
            )
            response["Content-Disposition"] = 'attachment; filename="split.pdf"'
            return response
        except ValidationError as exc:
            return JsonResponse({"error": exc.message}, status=400)
