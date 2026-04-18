from django.core.exceptions import ValidationError
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View

from ..services.memory import leer_subida
from ..services.pdf_operations import split_pdf


def _iterar_buffer(buffer, chunk_size=8192):
    while True:
        chunk = buffer.read(chunk_size)
        if not chunk:
            break
        yield chunk


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
