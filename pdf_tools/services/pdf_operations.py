"""Operaciones de PDF en memoria para endpoints de la API."""

from __future__ import annotations

import io
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.pdfgen import canvas


@dataclass(frozen=True)
class PageRange:
	inicio: int
	fin: int


def _to_output_buffer(writer: PdfWriter) -> io.BytesIO:
	output = io.BytesIO()
	writer.write(output)
	output.seek(0)
	return output


def merge_pdfs(buffers: list[io.BytesIO]) -> io.BytesIO:
	if len(buffers) < 2:
		raise ValidationError("Debes enviar al menos 2 archivos PDF para combinar.")

	writer = PdfWriter()
	for buffer in buffers:
		buffer.seek(0)
		reader = PdfReader(buffer)
		for page in reader.pages:
			writer.add_page(page)

	return _to_output_buffer(writer)


def _parse_page_ranges(paginas: str, total_paginas: int) -> list[PageRange]:
	if not paginas or not paginas.strip():
		raise ValidationError("Debes indicar las páginas en el campo 'paginas'.")

	rangos: list[PageRange] = []
	for parte in paginas.split(","):
		token = parte.strip()
		if not token:
			continue

		if "-" in token:
			start_s, end_s = token.split("-", 1)
			try:
				inicio = int(start_s)
				fin = int(end_s)
			except ValueError as exc:
				raise ValidationError(f"Rango inválido: '{token}'.") from exc
			if inicio < 1 or fin < 1 or inicio > fin:
				raise ValidationError(f"Rango inválido: '{token}'.")
			if fin > total_paginas:
				raise ValidationError(
					f"Rango fuera de límites: '{token}'. El PDF tiene {total_paginas} páginas."
				)
			rangos.append(PageRange(inicio, fin))
			continue

		try:
			pagina = int(token)
		except ValueError as exc:
			raise ValidationError(f"Número de página inválido: '{token}'.") from exc
		if pagina < 1 or pagina > total_paginas:
			raise ValidationError(
				f"Página fuera de límites: '{token}'. El PDF tiene {total_paginas} páginas."
			)
		rangos.append(PageRange(pagina, pagina))

	if not rangos:
		raise ValidationError("Debes indicar al menos una página válida.")

	return rangos


def split_pdf(buffer: io.BytesIO, paginas: str) -> io.BytesIO:
	buffer.seek(0)
	reader = PdfReader(buffer)
	total = len(reader.pages)
	rangos = _parse_page_ranges(paginas, total)

	writer = PdfWriter()
	for rango in rangos:
		for indice in range(rango.inicio - 1, rango.fin):
			writer.add_page(reader.pages[indice])

	return _to_output_buffer(writer)


def _parse_pages_list(raw_paginas: str | None, total_paginas: int) -> set[int] | None:
	if raw_paginas is None or not str(raw_paginas).strip():
		return None

	pages: set[int] = set()
	for token in str(raw_paginas).split(","):
		item = token.strip()
		if not item:
			continue
		try:
			numero = int(item)
		except ValueError as exc:
			raise ValidationError(f"Página inválida en 'paginas': '{item}'.") from exc
		if numero < 1 or numero > total_paginas:
			raise ValidationError(
				f"Página fuera de límites: '{item}'. El PDF tiene {total_paginas} páginas."
			)
		pages.add(numero)

	if not pages:
		raise ValidationError("'paginas' no contiene números válidos.")

	return pages


def rotate_pdf(buffer: io.BytesIO, angulo: int, paginas: str | None = None) -> io.BytesIO:
	if angulo not in {90, 180, 270}:
		raise ValidationError("Ángulo inválido. Solo se permiten 90, 180 o 270.")

	buffer.seek(0)
	reader = PdfReader(buffer)
	total = len(reader.pages)
	paginas_a_rotar = _parse_pages_list(paginas, total)

	writer = PdfWriter()
	for i, page in enumerate(reader.pages, start=1):
		if paginas_a_rotar is None or i in paginas_a_rotar:
			page.rotate(angulo)
		writer.add_page(page)

	return _to_output_buffer(writer)


def _build_watermark_page(texto: str, opacidad: float, width: float, height: float):
	wm_buffer = io.BytesIO()
	c = canvas.Canvas(wm_buffer, pagesize=(width, height))
	c.setFillColor(Color(0, 0, 0, alpha=opacidad))
	c.setFont("Helvetica", 32)
	c.drawCentredString(width / 2, height / 2, texto)
	c.save()
	wm_buffer.seek(0)
	return PdfReader(wm_buffer).pages[0]


def watermark_pdf(
	buffer: io.BytesIO,
	texto: str,
	opacidad: float = 0.2,
	posicion: str = "center",
) -> io.BytesIO:
	if not texto or not texto.strip():
		raise ValidationError("Debes enviar texto para la marca de agua en 'texto'.")
	if opacidad < 0 or opacidad > 1:
		raise ValidationError("La opacidad debe estar entre 0 y 1.")
	if posicion not in {"center"}:
		raise ValidationError("Posición inválida. Solo se soporta 'center'.")

	buffer.seek(0)
	reader = PdfReader(buffer)
	writer = PdfWriter()

	for page in reader.pages:
		width = float(page.mediabox.width)
		height = float(page.mediabox.height)
		wm_page = _build_watermark_page(texto.strip(), opacidad, width, height)
		page.merge_page(wm_page)
		writer.add_page(page)

	return _to_output_buffer(writer)


def generate_pdf(contenido: dict) -> io.BytesIO:
	if not isinstance(contenido, dict):
		raise ValidationError("El cuerpo JSON debe ser un objeto.")

	title = str(contenido.get("title", "Reporte PDF")).strip() or "Reporte PDF"
	sections = contenido.get("sections", [])
	if sections is None:
		sections = []
	if not isinstance(sections, list):
		raise ValidationError("'sections' debe ser una lista.")

	output = io.BytesIO()
	c = canvas.Canvas(output)
	width, height = c._pagesize
	y = height - 60

	c.setFont("Helvetica-Bold", 18)
	c.drawString(50, y, title)
	y -= 40

	for section in sections:
		if y < 80:
			c.showPage()
			y = height - 60

		if not isinstance(section, dict):
			continue

		section_type = section.get("type", "text")
		if section_type == "text":
			content = str(section.get("content", ""))
			c.setFont("Helvetica", 12)
			for line in content.splitlines() or [""]:
				c.drawString(50, y, line[:120])
				y -= 18
			y -= 8
			continue

		if section_type == "table":
			headers = section.get("headers") or []
			rows = section.get("rows") or []
			c.setFont("Helvetica-Bold", 11)
			c.drawString(50, y, " | ".join(str(h) for h in headers)[:120])
			y -= 18
			c.setFont("Helvetica", 10)
			for row in rows:
				row_values = row if isinstance(row, list) else [row]
				c.drawString(50, y, " | ".join(str(v) for v in row_values)[:120])
				y -= 16
				if y < 80:
					c.showPage()
					y = height - 60
			y -= 8

	c.save()
	output.seek(0)
	return output




