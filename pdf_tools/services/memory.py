# pdf_tools/services/memory.py
from __future__ import annotations

import io
from contextlib import contextmanager

from pypdf import PdfReader
from django.conf import settings
from django.core.exceptions import ValidationError

#Constantes 

MIME_PERMITIDO = "application/pdf"
CONTENT_TYPES_PERMITIDOS = {"application/pdf", "binary/octet-stream"}
MAX_BYTES_SUBIDA = int(getattr(settings, "MAX_UPLOAD_BYTES_MB", 20)) * 1024 * 1024



#Funcion para validar que el archivo es un PDF real
def _validate_pdf_bytes(buffer: io.BytesIO):
    """
    Verifica que el buffer contenga un PDF válido y sin contraseña.
    Lanza ValidationError si el archivo está corrupto o protegido.
    """
    # Verificar firma: todo PDF empieza con los bytes %PDF
    header = buffer.read(5)
    if header != b"%PDF-":
        raise ValidationError(
            "El archivo no es un PDF válido "
            "(la firma del archivo no corresponde a un PDF)."
        )
    buffer.seek(0)

    # Intentar abrir con pypdf para detectar corrupción o contraseña
    try:
        leer = PdfReader(buffer)
    except Exception:
        raise ValidationError(
            "El archivo PDF está corrupto o tiene un formato no soportado."
        )
    # Verificar si el PDF está protegido con contraseña
    if leer.is_encrypted:
        raise ValidationError(
            "El archivo PDF está protegido con contraseña. "
            "Desbloquéalo antes de subirlo."
        )
    
#Funcion para validar el archivo subido
def leer_subida(archivo_subido) -> io.BytesIO:
    """
    Recibe un InMemoryUploadedFile o TemporaryUploadedFile de Django
    y lo devuelve como un BytesIO limpio en RAM.

    Valida:
      - Que el archivo exista
      - Que el Content-Type sea PDF
      - Que no supere MAX_UPLOAD_BYTES_MB
      - Que el contenido sea un PDF real (no corrupto ni protegido)
    """
    # Verificar que le archivo exista
    if archivo_subido is None:
        raise ValidationError("No se envió ningún archivo.")
    
    # Validar el Content-Type declarado por el cliente
    content_TYPE = getattr(archivo_subido, "content_type", "")
    if content_TYPE not in CONTENT_TYPES_PERMITIDOS:
        raise ValidationError(
            f"Tipo de archivo no permitido: '{content_TYPE}'. "
            "Solo se aceptan archivos PDF."
        )
    
    # Validar el tamaño del archivo para que no supere el límite permitido
    if archivo_subido.size > MAX_BYTES_SUBIDA:
        max_mb = MAX_BYTES_SUBIDA // (1024 * 1024)
        raise ValidationError(
            f"El archivo supera el límite de {max_mb} MB "
            f"({archivo_subido.size / 1024 / 1024:.1f} MB recibidos)."
        )
    
    # Leer a BytesIO el archivo subido
    buffer = io.BytesIO()
    for chunk in archivo_subido.chunks():
        buffer.write(chunk)
    buffer.seek(0) 

    # Validar que es un PDF real
    _validate_pdf_bytes(buffer)
    buffer.seek(0)  # rebobinar de nuevo después de validar

    return buffer

#  Context manager para operaciones temporales con PDF
@contextmanager
def pdf_buffer(initial_bytes: bytes | None = None):
    """
    Context manager que entrega un BytesIO limpio y lo cierra al salir.

    Uso:
        with pdf_buffer() as buf:
            writer.write(buf)
            buf.seek(0)
            # usar buf aquí
        # al salir del with, buf.close() se llama automáticamente

    También acepta bytes iniciales:
        with pdf_buffer(some_bytes) as buf:
            reader = PdfReader(buf)
    """
    buf = io.BytesIO(initial_bytes) if initial_bytes else io.BytesIO()
    try:
        yield buf
    finally:
        buf.close()  # libera la memoria explícitamente


#  Helper para preparar la respuesta de salida 
def finalize_buffer(buffer: io.BytesIO) -> io.BytesIO:
    """
    Rebobina un BytesIO al inicio para que pueda ser leído por la respuesta HTTP.
    Llámado siempre antes de pasarle el buffer a StreamingHttpResponse.
    """
    buffer.seek(0)
    return buffer