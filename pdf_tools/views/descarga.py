# pdf_tools/views/descarga.py
from django.views import View
from django.core.exceptions import ValidationError
from django.http import StreamingHttpResponse, JsonResponse
from ..services.memory import leer_subida 
from .utils import _iterar_buffer

class DescargarPDFView(View):
    def post(self, request):
        """try:
            1. Obtener el archivo de request.FILES con "file"
            2. Llamar a leer_subida() — obtienes un BytesIO validado
            3. Crear StreamingHttpResponse pasándole _iterar_buffer(buffer)
            4. Asignar Content-Type y Content-Disposition a la response
            5. Retornar la response
                except ValidationError as e:
            6. Retornar JsonResponse con status 400 y e.message
        """

        try:
            archivo = request.FILES.get("file")
            buffer = leer_subida(archivo)
            response = StreamingHttpResponse(_iterar_buffer(buffer), content_type="application/pdf")
            response['Content-Disposition'] = 'attachment; filename="archivo.pdf"'
            return response
        except ValidationError as e:
            return JsonResponse({"error": e.message}, status=400) 