# 🗂️ PDF Tool — Herramienta Web de Manipulación de PDFs

> API REST de backend puro construida con **Django 5.2** para procesar archivos PDF íntegramente en memoria RAM, sin escritura en disco, con despliegue reproducible en **Docker** sobre entornos Unix.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat-square&logo=django&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/Licencia-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Estado-En%20desarrollo-orange?style=flat-square)

---

## Tabla de Contenidos

- [Descripción](#descripción)
- [Características](#características)
- [Arquitectura](#arquitectura)
- [Stack Tecnológico](#stack-tecnológico)
- [Requisitos Previos](#requisitos-previos)
- [Instalación y Ejecución](#instalación-y-ejecución)
- [Variables de Entorno](#variables-de-entorno)
- [Endpoints de la API](#endpoints-de-la-api)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Tests](#tests)
- [Seguridad](#seguridad)
- [Agregar una Nueva Operación](#agregar-una-nueva-operación)
- [Hoja de Ruta](#hoja-de-ruta)
- [Contribuir](#contribuir)

---

## Descripción

**PDF Tool** expone cinco operaciones sobre archivos PDF a través de una API REST. Todo el procesamiento ocurre en objetos `io.BytesIO` en memoria RAM: el archivo subido nunca toca el filesystem del servidor, y la respuesta se entrega como un stream HTTP directo.

El sistema está diseñado para integrarse en flujos de trabajo automatizados o como microservicio interno. No incluye interfaz de usuario — es backend puro.

---

## Características

- ✅ **Merge** — une múltiples PDFs en uno, en el orden que definas
- ✅ **Split** — divide un PDF por rangos de páginas (`1-3,5,7-9`) o una página por archivo (ZIP)
- ✅ **Rotate** — rota páginas específicas o todas (90 / 180 / 270°)
- ✅ **Watermark** — superpone una marca de agua (texto o imagen) con opacidad y posición configurables
- ✅ **Generate** — crea un PDF desde cero a partir de un JSON con texto, tablas e imágenes base64
- 🔒 **Cero archivos temporales** — procesamiento 100 % en `io.BytesIO`
- 🐳 **Docker-first** — imagen lista para producción con usuario non-root
- 🛡️ **Rate limiting** por IP, headers de seguridad HTTP y sanitización de nombres de archivo

---

## Arquitectura

```
Cliente HTTP
     │
     ▼
  Nginx (reverse proxy)
     │  client_max_body_size, proxy_read_timeout
     ▼
  Gunicorn (WSGI)
     │  workers, timeout, max_requests
     ▼
  Django 5.2
  ├── views/          ← endpoints REST (upload, merge, split, rotate, watermark, generate, download)
  ├── services/
  │   ├── memory.py   ← pipeline BytesIO: recibe stream → procesa en RAM → devuelve BytesIO
  │   └── pdf_operations.py  ← funciones puras: todas reciben y devuelven BytesIO
  └── utils/
      └── sanitize.py ← UUID interno, pathlib.Path.resolve(), validación MIME
```

El principio rector es **BytesIO como única frontera**: ninguna función dentro de `services/` conoce el filesystem. Reciben `BytesIO`, devuelven `BytesIO`. Las vistas se encargan de leer el request y escribir el `StreamingHttpResponse`.

---

## Stack Tecnológico

| Módulo | Herramienta | Versión |
|---|---|---|
| Framework web | Django | 5.2 |
| PDF — operaciones | PyPDF2 | ≥ 3.0 |
| PDF — generación y watermark | ReportLab | ≥ 4.0 |
| Gestión de memoria | `io.BytesIO` | stdlib |
| Servidor WSGI | Gunicorn | ≥ 21.0 |
| Proxy inverso | Nginx | ≥ 1.25 |
| Contenedor | Docker + Compose | v2 |
| Rate limiting | django-ratelimit | ≥ 4.0 |
| Headers de seguridad | django-csp | ≥ 3.7 |
| Gestión de secretos | python-decouple | ≥ 3.8 |
| Testing | pytest-django | ≥ 4.8 |
| Documentación API | drf-spectacular | ≥ 0.27 |

---

## Requisitos Previos

- **Docker** ≥ 24 y **Docker Compose** v2
- (Desarrollo local) Python 3.11+ y `pip`
- Unix: Arch Linux o Fedora (recomendado para producción)

---

## Instalación y Ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/pdf-tool.git
cd pdf-tool
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Edita .env con tus valores (ver sección Variables de Entorno)
```

### 3a. Levantar con Docker (recomendado)

```bash
docker-compose up --build
```

La API estará disponible en `http://localhost:80`.

### 3b. Desarrollo local sin Docker

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

La API estará disponible en `http://localhost:8000`.

---

## Variables de Entorno

Copia `.env.example` a `.env` y ajusta los valores:

```env
# Django
SECRET_KEY=cambia-esto-por-una-clave-segura
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Límites de archivos
MAX_UPLOAD_SIZE_MB=20

# Rate limiting (requests por minuto por IP en /api/*)
RATE_LIMIT_PER_MINUTE=10
```

> **Nunca** subas tu archivo `.env` al repositorio. Está incluido en `.gitignore`.

---

## Endpoints de la API

La documentación interactiva completa (OpenAPI 3.0) está disponible en `/api/schema/` una vez levantado el servidor.

### `POST /api/merge/`
Une múltiples PDFs en uno.

```bash
curl -X POST http://localhost/api/merge/ \
  -F "files=@documento1.pdf" \
  -F "files=@documento2.pdf" \
  --output resultado.pdf
```

### `POST /api/split/`
Divide un PDF por rangos de páginas.

```bash
# Páginas específicas (devuelve un ZIP con los fragmentos)
curl -X POST http://localhost/api/split/ \
  -F "file=@documento.pdf" \
  -F "pages=1-3,5,7-9" \
  --output fragmentos.zip

# Una página por archivo
curl -X POST http://localhost/api/split/ \
  -F "file=@documento.pdf" \
  -F "mode=one_per_page" \
  --output fragmentos.zip
```

### `POST /api/rotate/`
Rota páginas de un PDF.

```bash
# Rotar todas las páginas 90°
curl -X POST http://localhost/api/rotate/ \
  -F "file=@documento.pdf" \
  -F "angle=90" \
  --output rotado.pdf

# Rotar páginas específicas
curl -X POST http://localhost/api/rotate/ \
  -F "file=@documento.pdf" \
  -F "angle=180" \
  -F "pages=1,3,5" \
  --output rotado.pdf
```

### `POST /api/watermark/`
Agrega una marca de agua con texto o imagen.

```bash
curl -X POST http://localhost/api/watermark/ \
  -F "file=@documento.pdf" \
  -F "text=CONFIDENCIAL" \
  -F "opacity=0.3" \
  -F "position=center" \
  --output con_marca.pdf
```

### `POST /api/generate/`
Genera un PDF desde cero a partir de un JSON.

```bash
curl -X POST http://localhost/api/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Reporte Mensual",
    "sections": [
      { "type": "text", "content": "Resumen ejecutivo del mes de abril." },
      { "type": "table", "headers": ["Producto", "Ventas"], "rows": [["A", "120"], ["B", "85"]] }
    ]
  }' \
  --output reporte.pdf
```

### Códigos de respuesta

| Código | Descripción |
|---|---|
| `200` | Operación exitosa — cuerpo de la respuesta es el PDF o ZIP |
| `400` | Archivo inválido, tipo no soportado, PDF corrupto o parámetros incorrectos |
| `413` | Archivo supera el límite de tamaño (`MAX_UPLOAD_SIZE_MB`) |
| `429` | Rate limit excedido — demasiadas solicitudes desde la misma IP |
| `500` | Error interno del servidor |

---

## Estructura del Proyecto

```
pdf_tools/
├── middleware.py
├── urls.py
├── services/
│   ├── memory.py
│   └── pdf_operations.py
├── utils/
│   └── sanitize.py
└── views/
    ├── utils.py
    ├── subida.py
    ├── descarga.py
    ├── merge.py
    ├── split.py
    ├── rotate.py
    ├── watermark.py
    └── generate.py
tests/
├── conftest.py
├── test_fase2.py
├── test_fase3.py
└── test_fase4.py
nginx/
└── default.conf
openapi.yaml
docker-compose.yml
Dockerfile
```

---

## Tests

```bash
# Ejecutar todos los tests
pytest

# Con reporte de cobertura
pytest --cov=pdf_tools --cov-report=term-missing

# Solo tests unitarios (servicios)
pytest tests/test_services.py -v

# Solo tests de integración (endpoints)
pytest tests/test_endpoints.py -v
```

La suite verifica, entre otras cosas, que **ninguna operación genere archivos en el filesystem** del servidor:

```python
# Ejemplo de lo que verifica test_endpoints.py
def test_merge_no_temp_files(client, sample_pdfs):
    before = set(Path("/tmp").iterdir())
    response = client.post("/api/merge/", data={"files": sample_pdfs})
    after = set(Path("/tmp").iterdir())
    assert response.status_code == 200
    assert before == after  # ningún archivo nuevo en /tmp
```

---

## Seguridad

El sistema implementa múltiples capas de protección:

- **Usuario non-root** — el proceso dentro del contenedor corre como `pdf_worker` (UID 1001), sin acceso a recursos del sistema
- **Validación MIME** — se rechaza cualquier archivo que no sea `application/pdf`, independientemente de la extensión
- **UUID interno** — el nombre original del archivo nunca se usa en rutas internas; se genera un UUID en cada request
- **Path traversal** — todas las rutas internas se validan con `pathlib.Path.resolve()` antes de cualquier operación
- **Rate limiting** — `django-ratelimit` aplica un límite por IP en todos los endpoints `/api/*`
- **Headers HTTP** — `Content-Security-Policy`, `X-Frame-Options: DENY` y `X-Content-Type-Options: nosniff` en todas las respuestas
- **CSRF** — habilitado en todos los endpoints que modifican estado

---

## Agregar una Nueva Operación

El sistema está diseñado para extenderse fácilmente. Para agregar, por ejemplo, un endpoint de compresión:

**1.** Agrega la función pura en `services/pdf_operations.py`:

```python
def compress_pdf(input_buffer: BytesIO, quality: str = "medium") -> BytesIO:
    """Comprime un PDF. Recibe BytesIO, devuelve BytesIO."""
    output = BytesIO()
    # ... lógica de compresión ...
    output.seek(0)
    return output
```

**2.** Crea la vista en `views/compress.py`:

```python
from django.views import View
from ratelimit.decorators import ratelimit
from ..services.memory import read_upload
from ..services.pdf_operations import compress_pdf

class CompressView(View):
    @ratelimit(key="ip", rate="10/m", block=True)
    def post(self, request):
        buffer = read_upload(request.FILES.get("file"))
        result = compress_pdf(buffer, quality=request.POST.get("quality", "medium"))
        return streaming_pdf_response(result, "compressed.pdf")
```

**3.** Registra la URL en `urls.py`:

```python
path("api/compress/", CompressView.as_view(), name="compress"),
```

**4.** Agrega tests en `tests/test_services.py` y `tests/test_endpoints.py` con fixtures reales.

---

## Hoja de Ruta

- [x] Fase 1 — Configuración del entorno y estructura del proyecto
- [x] Fase 2 — Pipeline BytesIO y módulo de memoria
- [x] Fase 3 — Cinco operaciones PDF (merge, split, rotate, watermark, generate)
- [x] Fase 4 — Seguridad y hardening (non-root, rate limiting, headers)
- [x] Fase 5 — Tests completos, documentación OpenAPI y stack de producción

---

## Contribuir

1. Haz fork del repositorio
2. Crea una rama para tu feature: `git checkout -b feature/nombre-operacion`
3. Escribe los tests **antes** de implementar (TDD recomendado)
4. Asegúrate de que `pytest` pasa sin errores y la cobertura no baja del 80 %
5. Abre un Pull Request describiendo el cambio y los tests agregados

---

> Proyecto desarrollado como parte del ecosistema **Backend & Automatización**.  
> Duración estimada: 7 semanas · 5 fases · Django 5.2 · Python 3.11+ · Docker · Unix
