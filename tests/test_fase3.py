import io
import json

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from pypdf import PdfReader, PdfWriter


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


def _contenido_respuesta(response):
	if getattr(response, "streaming", False):
		return b"".join(response.streaming_content)
	return response.content


def _build_pdf_paginas(cantidad: int) -> bytes:
	base = PdfReader(io.BytesIO(PDF_MINIMO))
	writer = PdfWriter()
	for _ in range(cantidad):
		writer.add_page(base.pages[0])
	output = io.BytesIO()
	writer.write(output)
	return output.getvalue()


@pytest.fixture
def pdf_valido():
	return SimpleUploadedFile(
		"test.pdf",
		PDF_MINIMO,
		content_type="application/pdf",
	)


@pytest.fixture
def pdf_dos_paginas():
	return SimpleUploadedFile(
		"dos_paginas.pdf",
		_build_pdf_paginas(2),
		content_type="application/pdf",
	)


def test_merge_exitoso(client, pdf_valido):
	segundo = SimpleUploadedFile("test2.pdf", PDF_MINIMO, content_type="application/pdf")
	response = client.post("/api/merge/", data={"files": [pdf_valido, segundo]})

	assert response.status_code == 200
	assert response.headers["Content-Type"] == "application/pdf"
	contenido = _contenido_respuesta(response)
	assert len(PdfReader(io.BytesIO(contenido)).pages) == 2


def test_merge_requiere_multiples_archivos(client, pdf_valido):
	response = client.post("/api/merge/", data={"files": [pdf_valido]})

	assert response.status_code == 400
	assert "al menos 2" in response.json()["error"]


def test_split_exitoso(client, pdf_dos_paginas):
	response = client.post(
		"/api/split/",
		data={"file": pdf_dos_paginas, "paginas": "2"},
	)

	assert response.status_code == 200
	contenido = _contenido_respuesta(response)
	assert len(PdfReader(io.BytesIO(contenido)).pages) == 1


def test_rotate_exitoso(client, pdf_valido):
	response = client.post(
		"/api/rotate/",
		data={"file": pdf_valido, "angulo": "90"},
	)

	assert response.status_code == 200
	contenido = _contenido_respuesta(response)
	reader = PdfReader(io.BytesIO(contenido))
	assert len(reader.pages) == 1
	assert int(reader.pages[0].get("/Rotate", 0)) == 90


def test_watermark_exitoso(client, pdf_valido):
	response = client.post(
		"/api/watermark/",
		data={"file": pdf_valido, "texto": "CONFIDENCIAL", "opacidad": "0.3"},
	)

	assert response.status_code == 200
	contenido = _contenido_respuesta(response)
	assert len(PdfReader(io.BytesIO(contenido)).pages) == 1


def test_generate_exitoso(client):
	payload = {
		"title": "Reporte",
		"sections": [
			{"type": "text", "content": "Resumen de prueba"},
			{"type": "table", "headers": ["A", "B"], "rows": [[1, 2]]},
		],
	}
	response = client.post(
		"/api/generate/",
		data=json.dumps(payload),
		content_type="application/json",
	)

	assert response.status_code == 200
	assert response.headers["Content-Type"] == "application/pdf"
	contenido = _contenido_respuesta(response)
	assert len(PdfReader(io.BytesIO(contenido)).pages) >= 1


def test_generate_json_invalido(client):
	response = client.post(
		"/api/generate/",
		data="{json-roto}",
		content_type="application/json",
	)

	assert response.status_code == 400
	assert "JSON válido" in response.json()["error"]
