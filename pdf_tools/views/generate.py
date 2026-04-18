import json

from django.core.exceptions import ValidationError
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View

from ..services.pdf_operations import generate_pdf


def _iterar_buffer(buffer, chunk_size=8192):
    while True:
        chunk = buffer.read(chunk_size)
        if not chunk:
            break
        yield chunk


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
