# pdf_tools/views/subida.py
from django.views import View
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from ..services.memory import leer_subida
from pypdf import PdfReader


#clase para manejar la subida de archivos PDF
class SubidaPDFView(View):

    def post(self, request):
        """
        1. Obtener el archivo de request.FILES con la clave "file"
        2. Llamar a leer_subida() con ese archivo
        3. Retornar JsonResponse con status 200 y un mensaje de éxito
            — incluye cuántas páginas tiene el PDF (pista: abre el buffer
            con PdfReader y lee len(reader.pages))
            except ValidationError as e:
        4. Retornar JsonResponse con status 400 y e.message como error
          """
        try:
            archivo_subido = request.FILES.get("file")
            buffer = leer_subida(archivo_subido)
            reader = PdfReader(buffer)
            num_paginas = len(reader.pages) 
            return JsonResponse({"message": "Archivo PDF subido exitosamente.", "num_paginas": num_paginas}, status=200)
        except ValidationError as e:
            return JsonResponse({"error": e.message}, status=400)

