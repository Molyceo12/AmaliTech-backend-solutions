from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class ProcessPaymentAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/api/auth/process-payment/':
            # Debug log to Render Console
            print(f"[AUTH_CHECK] Processing request for: {request.path}")
            
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return JsonResponse({"success": False, "message": "Auth header missing"}, status=401)

            try:
                jwt_authenticator = JWTAuthentication()
                header = jwt_authenticator.get_header(request)
                raw_token = jwt_authenticator.get_raw_token(header)
                validated_token = jwt_authenticator.get_validated_token(raw_token)
                
                # Get the User ID stored in the token
                user_id = validated_token.get('user_id')
                print(f"[AUTH_CHECK] Token is valid. Looking for User ID: {user_id}")

                user = jwt_authenticator.get_user(validated_token)
                
                if user is None:
                    # Check if ANY users exist in the DB
                    user_count = User.objects.count()
                    print(f"[AUTH_CHECK] FAILURE: User {user_id} not found in DB. Total users in DB: {user_count}")
                    
                    return JsonResponse({
                        "success": False,
                        "message": f"User {user_id} not found. DB reset detected. Total users in DB now: {user_count}. Please re-register."
                    }, status=401)
                
                print(f"[AUTH_CHECK] SUCCESS: Found user {user.email}")
                request.user = user
                
            except Exception as e:
                print(f"[AUTH_CHECK] ERROR: {str(e)}")
                return JsonResponse({"success": False, "message": "Authentication failed"}, status=401)

        return self.get_response(request)
