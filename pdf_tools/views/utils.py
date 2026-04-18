

from django.http import JsonResponse


def _iterar_buffer(buffer, chunk_size=8192):
    while True:
        chunk = buffer.read(chunk_size)
        if not chunk:
            break
        yield chunk


def ratelimited_error(request, exception=None):
    return JsonResponse(
        {"error": "Demasiadas solicitudes. Intenta nuevamente en un minuto."},
        status=429,
    )
