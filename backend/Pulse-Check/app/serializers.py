from rest_framework import serializers
from .models import Monitor

class MonitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Monitor
        fields = ['id', 'timeout', 'alert_email', 'status', 'last_heartbeat']
        read_only_fields = ['status', 'last_heartbeat']

    def validate_timeout(self, value):
        if value <= 0:
            raise serializers.ValidationError("Timeout must be a positive integer.")
        return value

    def validate_id(self, value):
        if not value.strip():
            raise serializers.ValidationError("Device ID cannot be empty.")
        return value
