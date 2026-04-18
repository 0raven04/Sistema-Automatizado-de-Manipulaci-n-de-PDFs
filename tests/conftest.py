import io

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
	return SimpleUploadedFile("test.pdf", PDF_MINIMO, content_type="application/pdf")


@pytest.fixture
def pdf_dos_paginas():
	return SimpleUploadedFile(
		"dos_paginas.pdf",
		_build_pdf_paginas(2),
		content_type="application/pdf",
	)
