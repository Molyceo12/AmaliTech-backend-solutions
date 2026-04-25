from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class ProcessPaymentAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/api/auth/process-payment/':
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return JsonResponse({
                    "success": False,
                    "message": "Authentication token is required for this API"
                }, status=401)

            try:
                jwt_authenticator = JWTAuthentication()
                auth_result = jwt_authenticator.authenticate(request)
                
                if auth_result is None:
                    raise AuthenticationFailed("Invalid or expired token")
                
                request.user = auth_result[0]
                
            except Exception:
                return JsonResponse({
                    "success": False,
                    "message": "Invalid or expired token"
                }, status=401)

        response = self.get_response(request)
        return response
