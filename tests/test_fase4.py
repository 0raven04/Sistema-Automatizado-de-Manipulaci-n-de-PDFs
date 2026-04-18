from pathlib import Path

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import override_settings

from pdf_tools.utils.sanitize import generar_id_operacion, validar_ruta
from .conftest import PDF_MINIMO


def _nuevo_pdf(nombre: str = "t.pdf") -> SimpleUploadedFile:
	return SimpleUploadedFile(nombre, PDF_MINIMO, content_type="application/pdf")


def test_headers_seguridad_en_respuesta_exitosa(client, pdf_valido):
	response = client.post("/api/upload/", data={"file": pdf_valido})

	assert response.status_code == 200
	assert response.headers["X-Content-Type-Options"] == "nosniff"
	assert response.headers["X-Frame-Options"] == "DENY"
	assert "default-src" in response.headers["Content-Security-Policy"]


def test_headers_seguridad_en_respuesta_error(client):
	response = client.post("/api/upload/", data={})

	assert response.status_code == 400
	assert response.headers["X-Content-Type-Options"] == "nosniff"
	assert response.headers["X-Frame-Options"] == "DENY"
	assert "default-src" in response.headers["Content-Security-Policy"]


@override_settings(RATELIMIT_ENABLE=True)
def test_rate_limit_devuelve_429(client):
	cache.clear()

	for i in range(10):
		response = client.post(
			"/api/merge/",
			data={"files": [_nuevo_pdf(f"a{i}.pdf"), _nuevo_pdf(f"b{i}.pdf")]},
		)
		assert response.status_code != 429

	response = client.post(
		"/api/merge/",
		data={"files": [_nuevo_pdf("a-final.pdf"), _nuevo_pdf("b-final.pdf")]},
	)
	assert response.status_code == 429


def test_ids_unicos():
	ids = {generar_id_operacion() for _ in range(100)}
	assert len(ids) == 100


def test_path_traversal_detectado():
	base = Path("/app/uploads")
	maliciosa = Path("/app/uploads/../../etc/passwd")

	with pytest.raises(ValidationError):
		validar_ruta(base, maliciosa)


def test_ruta_valida_pasa():
	base = Path("/app/uploads")
	valida = Path("/app/uploads/documento.pdf")

	resultado = validar_ruta(base, valida)
	assert resultado == valida.resolve()
