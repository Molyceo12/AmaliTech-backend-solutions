from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.cache import cache

from .models import Monitor
from .serializers import MonitorSerializer
from .timers import start_monitor_timer, cancel_monitor_timer

class MonitorListView(generics.ListAPIView):
    queryset = Monitor.objects.all()
    serializer_class = MonitorSerializer

class MonitorCreateView(generics.CreateAPIView):
    queryset = Monitor.objects.all()
    serializer_class = MonitorSerializer

    def perform_create(self, serializer):
        monitor = serializer.save()
        
        # Redis: Track real-time activity with TTL
        redis_key = f"active_monitor_{monitor.id}"
        cache.set(redis_key, True, timeout=monitor.timeout)
        
        # setTimeout: Start background timer
        start_monitor_timer(monitor.id, monitor.timeout)

class HeartbeatView(APIView):
    def post(self, request, pk):
        monitor = get_object_or_404(Monitor, id=pk)
        
        # 1. Update Database (Persistence)
        monitor.last_heartbeat = timezone.now()
        monitor.status = Monitor.Status.ACTIVE
        monitor.save(update_fields=['last_heartbeat', 'status'])
        
        # 2. Update Redis: Reset TTL
        redis_key = f"active_monitor_{monitor.id}"
        cache.set(redis_key, True, timeout=monitor.timeout)
        
        # 3. Restart setTimeout
        start_monitor_timer(monitor.id, monitor.timeout)
        
        return Response({"success": True, "message": "Heartbeat received, Redis TTL reset."}, status=status.HTTP_200_OK)

class PauseView(APIView):
    def post(self, request, pk):
        monitor = get_object_or_404(Monitor, id=pk)
        
        # 1. Update Database
        monitor.status = Monitor.Status.PAUSED
        monitor.save(update_fields=['status'])
        
        # 2. Delete Redis Key
        redis_key = f"active_monitor_{monitor.id}"
        cache.delete(redis_key)
        
        # 3. Cancel setTimeout
        cancel_monitor_timer(monitor.id)
        
        return Response({"success": True, "message": "Monitoring paused."}, status=status.HTTP_200_OK)
