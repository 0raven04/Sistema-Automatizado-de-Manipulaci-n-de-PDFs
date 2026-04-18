




from django.http import JsonResponse
from django_ratelimit.exceptions import Ratelimited


class SecurityHeadersMiddleware:
    """
    Middleware to set security-related HTTP headers.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Ratelimited:
            response = JsonResponse(
                {"error": "Demasiadas solicitudes. Intenta nuevamente en un minuto."},
                status=429,
            )

        # Set security headers
        response["Content-Security-Policy"] = "default-src 'none'"
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"

        return response