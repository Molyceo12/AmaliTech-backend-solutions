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
        redis_key = f"active_monitor_{monitor.id}"
        cache.set(redis_key, True, timeout=monitor.timeout)
        start_monitor_timer(monitor.id, monitor.timeout)

class HeartbeatView(APIView):
    def post(self, request, pk):
        monitor = get_object_or_404(Monitor, id=pk)
        was_down = (monitor.status == Monitor.Status.DOWN)
        monitor.last_heartbeat = timezone.now()
        monitor.status = Monitor.Status.ACTIVE
        monitor.save(update_fields=['last_heartbeat', 'status'])
        
        redis_key = f"active_monitor_{monitor.id}"
        cache.set(redis_key, True, timeout=monitor.timeout)
        start_monitor_timer(monitor.id, monitor.timeout)
        
        message = "Heartbeat received. Device is active."
        if was_down:
            message = "Heartbeat received. Device restored from DOWN state."
            
        return Response({
            "success": True, 
            "message": message,
            "id": monitor.id
        }, status=status.HTTP_200_OK)

class PauseView(APIView):
    def post(self, request, pk):
        monitor = get_object_or_404(Monitor, id=pk)
        if monitor.status == Monitor.Status.PAUSED:
            return Response({"success": True, "message": "Device is already paused."}, status=status.HTTP_200_OK)
            
        monitor.status = Monitor.Status.PAUSED
        monitor.save(update_fields=['status'])
        
        redis_key = f"active_monitor_{monitor.id}"
        cache.delete(redis_key)
        cancel_monitor_timer(monitor.id)
        
        return Response({
            "success": True, 
            "message": f"Monitoring paused for {monitor.id}."
        }, status=status.HTTP_200_OK)

class MonitorStatusView(generics.RetrieveAPIView):
    queryset = Monitor.objects.all()
    serializer_class = MonitorSerializer
