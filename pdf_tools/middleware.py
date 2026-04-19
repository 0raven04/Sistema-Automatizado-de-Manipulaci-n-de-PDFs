from django.http import JsonResponse
from django_ratelimit.exceptions import Ratelimited


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Swagger UI necesita cargar assets externos
        if request.path.startswith("/api/docs") or request.path.startswith("/api/schema"):
            response["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "img-src 'self' data:;"
            )
        else:
            response["Content-Security-Policy"] = "default-src 'none'"

        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        return response