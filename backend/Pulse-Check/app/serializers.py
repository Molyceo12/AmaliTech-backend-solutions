from rest_framework import serializers
from .models import Monitor

class MonitorSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    last_heartbeat = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Monitor
        fields = ['id', 'timeout', 'alert_email', 'status', 'last_heartbeat']
