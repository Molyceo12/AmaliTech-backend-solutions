import hashlib
import json
import time

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import LoginSerializer, RegisterSerializer

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

class ProcessPaymentView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        amount_raw = request.data.get('amount')
        currency = request.data.get('currency')

        if amount_raw is None or currency is None:
            return Response({"error": "Missing amount or currency"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = float(amount_raw)
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            return Response({"error": "Amount must be a positive number"}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(currency, str) or not currency.strip():
            return Response({"error": "Invalid currency"}, status=status.HTTP_400_BAD_REQUEST)

        rate_key = f"rate_limit:{request.user.id}"
        request_count = cache.get(rate_key, 0)
        
        if request_count >= 5:
            return Response({"error": "Too many requests. Please wait 60 seconds."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
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

        request_body_hash = hashlib.sha256(json.dumps(request.data, sort_keys=True).encode()).hexdigest()
        redis_key = f"idempotent_txn:{request.user.id}:{idempotency_key}"
        
        lock_init = {
            "status": "PROCESSING",
            "body_hash": request_body_hash
        }
        
        is_new = cache.set(redis_key, json.dumps(lock_init), timeout=3600, nx=True)

        if not is_new:
            cached_val = json.loads(cache.get(redis_key))
            
            if cached_val.get('body_hash') != request_body_hash:
                return Response({
                    "success": False,
                    "message": "Idempotency key usage conflict: different request body detected."
                }, status=status.HTTP_409_CONFLICT)

            while cached_val.get('status') == 'PROCESSING':
                time.sleep(0.5)
                raw_payload = cache.get(redis_key)
                if not raw_payload: break
                cached_val = json.loads(raw_payload)
            
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
                user.save(update_fields=['balance'])
                
                response_data = {
                    "success": True,
                    "message": f"Successfully charged {amount} {currency}",
                    "data": {
                        "transaction_id": f"txn_{int(time.time())}",
                        "amount": amount,
                        "currency": currency,
                        "remaining_balance": float(user.balance)
                    }
                }
                status_code = status.HTTP_201_CREATED

            final_payload = {
                "status": "COMPLETED",
                "body_hash": request_body_hash,
                "response_data": response_data,
                "status_code": status_code
            }
            cache.set(redis_key, json.dumps(final_payload), timeout=86400)

            return Response(response_data, status=status_code)
            
        except Exception as e:
            cache.delete(redis_key)
            return Response({
                "success": False, 
                "message": "Internal gateway error during processing."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
