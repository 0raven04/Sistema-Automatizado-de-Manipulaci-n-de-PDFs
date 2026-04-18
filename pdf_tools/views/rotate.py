from django.core.exceptions import ValidationError
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View

from ..services.memory import leer_subida
from ..services.pdf_operations import rotate_pdf


def _iterar_buffer(buffer, chunk_size=8192):
    while True:
        chunk = buffer.read(chunk_size)
        if not chunk:
            break
        yield chunk


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

            paginas = request.POST.get("paginas")
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
