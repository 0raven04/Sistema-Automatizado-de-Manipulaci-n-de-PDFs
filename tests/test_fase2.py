import io
import pytest
from pathlib import Path
from django.core.files.uploadedfile import SimpleUploadedFile
from pypdf import PdfReader

# PDF mínimo válido definido como constante — sin archivos en disco
PDF_MINIMO = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
    b"xref\n0 4\n" 
    b"0000000000 65535 f\n"
    b"0000000009 00000 n\n"
    b"0000000058 00000 n\n"
    b"0000000115 00000 n\n"
    b"trailer<</Size 4/Root 1 0 R>>\n"
    b"startxref\n190\n%%EOF"
)

# Fixture reutilizable para no repetir SimpleUploadedFile en cada test.
@pytest.fixture
def pdf_valido():
    return SimpleUploadedFile("test.pdf", PDF_MINIMO, content_type="application/pdf")


def _obtener_contenido_respuesta(response):
    if getattr(response, "streaming", False):
        return b"".join(response.streaming_content)
    return response.content


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

    contenido = _obtener_contenido_respuesta(response)
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