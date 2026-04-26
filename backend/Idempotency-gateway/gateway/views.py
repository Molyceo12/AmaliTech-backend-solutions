from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegisterSerializer, LoginSerializer
from django.contrib.auth import get_user_model
import time
import json
from django.core.cache import cache

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "success": True,
                "message": "User registered successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "success": False,
            "message": "Registration failed",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class LoginView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return Response({
                "success": True,
                "message": "Login successful",
                "data": serializer.validated_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Invalid credentials",
                "errors": str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)


import hashlib

class ProcessPaymentView(generics.GenericAPIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        amount_raw = request.data.get('amount')
        currency = request.data.get('currency')

        if amount_raw is None or currency is None:
            return Response({"error": "Missing amount or currency"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = float(amount_raw)
            if amount <= 0:
                return Response({"error": "Amount must be a positive number"}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({"error": "Invalid amount format"}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(currency, str) or not currency.strip():
            return Response({"error": "Invalid currency"}, status=status.HTTP_400_BAD_REQUEST)

        request_body_hash = hashlib.sha256(json.dumps(request.data, sort_keys=True).encode()).hexdigest()

        rate_key = f"rate:{request.user.id}"
        request_count = cache.get(rate_key, 0)
        
        if request_count >= 5:
            return Response({"error": "Too many requests"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        if request_count == 0:
            cache.set(rate_key, 1, timeout=60)
        else:
            cache.incr(rate_key)

        idempotency_key = request.headers.get('Idempotency-Key')
        if not idempotency_key:
            return Response({
                "success": False,
                "message": "Idempotency-Key header is required",
            }, status=status.HTTP_400_BAD_REQUEST)

        redis_key = f"idempotency:{request.user.id}:{idempotency_key}"
        
        lock_data = {
            "status": "STARTED",
            "body_hash": request_body_hash
        }
        
        is_new = cache.set(redis_key, json.dumps(lock_data), timeout=3600, nx=True)

        if not is_new:
            cached_val = json.loads(cache.get(redis_key))
            
            if cached_val.get('body_hash') != request_body_hash:
                return Response({
                    "success": False,
                    "message": "Idempotency key already used for a different request body."
                }, status=status.HTTP_409_CONFLICT)

            while cached_val.get('status') == 'STARTED':
                time.sleep(0.5)
                raw_val = cache.get(redis_key)
                if not raw_val: break # Should not happen with long TTL
                cached_val = json.loads(raw_val)
            
            return Response(
                cached_val.get('response_data'), 
                status=cached_val.get('status_code'),
                headers={'X-Cache-Hit': 'true'}
            )

        try:
            time.sleep(2)
            user = request.user
            
            if user.balance < amount:
                response_data = {
                    "success": False,
                    "message": "Insufficient balance",
                    "current_balance": float(user.balance)
                }
                status_code = status.HTTP_400_BAD_REQUEST
            else:
                user.balance = float(user.balance) - amount
                user.save()
                response_data = {
                    "success": True,
                    "message": f"Charged {amount} {currency}",
                    "data": {
                        "transaction_id": f"txn_{int(time.time())}",
                        "amount": amount,
                        "currency": currency,
                        "remaining_balance": float(user.balance)
                    }
                }
                status_code = status.HTTP_201_CREATED

            
            final_data = {
                "status": "COMPLETED",
                "body_hash": request_body_hash,
                "response_data": response_data,
                "status_code": status_code
            }
            cache.set(redis_key, json.dumps(final_data), timeout=86400)

            return Response(response_data, status=status_code)
            
        except Exception as e:
           
            cache.delete(redis_key)
            return Response({"success": False, "message": str(e)}, status=500)
