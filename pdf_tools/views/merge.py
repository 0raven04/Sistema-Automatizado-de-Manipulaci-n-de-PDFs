from django.core.exceptions import ValidationError
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View

from ..services.memory import leer_subida
from ..services.pdf_operations import merge_pdfs


def _iterar_buffer(buffer, chunk_size=8192):
    while True:
        chunk = buffer.read(chunk_size)
        if not chunk:
            break
        yield chunk


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
