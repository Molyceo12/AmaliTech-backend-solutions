import threading
import logging
from django.core.cache import cache
from django.utils import timezone
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

# Dictionary to store active timers: {device_id: threading.Timer}
active_timers = {}

def trigger_alert(device_id):
    """
    The function executed when 'setTimeout' (Timer) expires.
    It checks Redis; if the key is gone, it means the device failed.
    """
    from .models import Monitor
    
    # Check if Redis still has the active key
    redis_key = f"active_monitor_{device_id}"
    is_active = cache.get(redis_key)
    
    if not is_active:
        try:
            monitor = Monitor.objects.get(id=device_id)
            if monitor.status == Monitor.Status.PAUSED:
                return # Don't alert if paused

            # 1. Update Database
            monitor.status = Monitor.Status.DOWN
            monitor.save(update_fields=['status'])

            # 2. Console JSON Alert
            alert_json = {
                "ALERT": f"Device {device_id} is down!",
                "time": timezone.now().isoformat(),
                "alert_email": monitor.alert_email
            }
            print("\n*** CRITICAL ALERT (TIMEOUT EXPIRED) ***")
            import json
            print(json.dumps(alert_json, indent=2))
            print("****************************************\n")

            # 3. Simulated Email
            send_mail(
                subject=f"CRITICAL: Device {device_id} is Offline!",
                message=f"CritMon Alert: Device {device_id} failed to signal in time.",
                from_email="system@critmon.com",
                recipient_list=[monitor.alert_email],
                fail_silently=False,
            )
            print(f"✅ Alert email virtually sent to {monitor.alert_email}")

        except Monitor.DoesNotExist:
            pass
    
    # Clean up the timer reference
    if device_id in active_timers:
        del active_timers[device_id]

def start_monitor_timer(device_id, timeout_seconds):
    """
    Equivalent to setTimeout(). 
    It clears any existing timer and starts a new one.
    """
    # Cancel existing timer if any
    if device_id in active_timers:
        active_timers[device_id].cancel()

    # Start new timer
    # We add 1 second of grace period to let Redis TTL expire naturally first
    wait_time = timeout_seconds + 1
    t = threading.Timer(wait_time, trigger_alert, args=[device_id])
    active_timers[device_id] = t
    t.start()

def cancel_monitor_timer(device_id):
    """Equivalent to clearTimeout()"""
    if device_id in active_timers:
        active_timers[device_id].cancel()
        del active_timers[device_id]
