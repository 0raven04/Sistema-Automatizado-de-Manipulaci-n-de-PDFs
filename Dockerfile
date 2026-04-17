FROM python:3.11-slim

# Evitar archivos .pyc y habilitar logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dependencias mínimas de sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc python3-dev curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Crear usuario sin privilegios para Fedora/Docker
RUN useradd -m pdf_worker
USER pdf_worker
WORKDIR /home/pdf_worker/app

# Instalar dependencias
COPY --chown=pdf_worker:pdf_worker requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copiar el resto del código
COPY --chown=pdf_worker:pdf_worker . .

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]