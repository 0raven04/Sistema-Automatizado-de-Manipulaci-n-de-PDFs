from django.core.exceptions import ValidationError
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View

from ..services.memory import leer_subida
from ..services.pdf_operations import watermark_pdf


def _iterar_buffer(buffer, chunk_size=8192):
    while True:
        chunk = buffer.read(chunk_size)
        if not chunk:
            break
        yield chunk


class WatermarkPDFView(View):
    def post(self, request):
        try:
            archivo = request.FILES.get("file")
            texto = request.POST.get("texto", "")
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
