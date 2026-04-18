import io
import pytest
from pathlib import Path
from django.core.files.uploadedfile import SimpleUploadedFile
from pypdf import PdfReader

from .conftest import _contenido_respuesta

#Test 1 - upload exitoso
"""
Sube PDF_MINIMO, verifica status_code == 200 y que la respuesta JSON 
contiene las claves "message" y "num_paginas".
"""
def test_upload_pdf_minimo(client, pdf_valido):
    response = client.post("/api/upload/", data={"file": pdf_valido})

    assert response.status_code == 200

    json_response = response.json()
    assert json_response["message"] == "Archivo PDF subido exitosamente."
    assert json_response["num_paginas"] == 1


#Test 2 — upload sin archivo   
"""
Haz POST /api/upload/ sin ningún archivo en data.
Verifica status_code == 400 y que la respuesta JSON contiene la clave "error".
"""
def test_upload_sin_archivo(client):
    response = client.post("/api/upload/", data={})

    assert response.status_code == 400
    assert response.json()["error"] == "No se envió ningún archivo."

#Test 3 — upload con archivo que no es PDF
"""
Crea un SimpleUploadedFile con content=b"esto no es un pdf" y 
content_type="application/pdf". Verifica status_code == 400.
"""
def test_upload_archivo_no_pdf(client):
    archivo = SimpleUploadedFile(
        "archivo.txt",
        b"esto no es un pdf",
        content_type="application/pdf",
    )

    response = client.post("/api/upload/", data={"file": archivo})

    assert response.status_code == 400
    assert "no es un PDF válido" in response.json()["error"]

#Test 4 — upload con tipo MIME incorrecto
"""
Crea un SimpleUploadedFile con content_type="image/jpeg".
Verifica status_code == 400.
"""
def test_upload_tipo_mime_incorrecto(client):
    archivo = SimpleUploadedFile(
        "imagen.jpg",
        b"esto es una imagen",
        content_type="image/jpeg",
    )

    response = client.post("/api/upload/", data={"file": archivo})

    assert response.status_code == 400
    assert "Solo se aceptan archivos PDF" in response.json()["error"]

#Test 5 — descarga exitosa
"""
Sube PDF_MINIMO a POST /api/download/, verifica status_code == 200,
que Content-Type es application/pdf y que Content-Disposition contiene attachment.
"""
def test_download_exitoso(client, pdf_valido):
    response = client.post("/api/download/", data={"file": pdf_valido})

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert "attachment" in response.headers.get("Content-Disposition", "")

    contenido = _contenido_respuesta(response)
    reader = PdfReader(io.BytesIO(contenido))
    assert len(reader.pages) == 1

#Test 6 — cero archivos en disco
"""
Este es el más importante. Antes del request a /api/download/ captura set(Path("/tmp").iterdir()).
Después del request verifica que el conjunto no cambió.
"""
def test_download_sin_archivo(client):
    response = client.post("/api/download/", data={})

    assert response.status_code == 400
    assert response.json()["error"] == "No se envió ningún archivo."

def test_cero_archivos_en_disco(client, pdf_valido):
    antes = set(Path("/tmp").iterdir())
    client.post("/api/download/", data={"file": pdf_valido})
    despues = set(Path("/tmp").iterdir())
    assert antes == despues