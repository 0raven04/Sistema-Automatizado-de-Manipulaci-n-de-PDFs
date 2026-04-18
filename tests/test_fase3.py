import io
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from pypdf import PdfReader

from .conftest import PDF_MINIMO, _contenido_respuesta


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

#test_split_rango_fuera_de_limites — paginas="1-10" en pdf de 2 páginas

def test_split_rango_fuera_de_limites(client, pdf_dos_paginas):
	response = client.post(
		"/api/split/",
		data={"file": pdf_dos_paginas, "paginas": "1-10"},
	)

	assert response.status_code == 400
	assert "fuera de límites" in response.json()["error"]

#test_rotate_angulo_invalido — angulo="45"

def test_rotate_angulo_invalido(client, pdf_valido):
	response = client.post(
		"/api/rotate/",
		data={"file": pdf_valido, "angulo": "45"},
	)

	assert response.status_code == 400
	assert "Ángulo inválido" in response.json()["error"]

#test_watermark_sin_texto — sin campo texto


def test_watermark_sin_texto(client, pdf_valido):
	response = client.post(
		"/api/watermark/",
		data={"file": pdf_valido, "opacidad": "0.3"},
	)

	assert response.status_code == 400
	assert "Debes enviar el texto" in response.json()["error"]