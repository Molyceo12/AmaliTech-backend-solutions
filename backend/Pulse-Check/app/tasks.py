import json
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from .models import Monitor

@shared_task
def trigger_alert_task(device_id):
    try:
        monitor = Monitor.objects.get(id=device_id)
        monitor.status = Monitor.Status.DOWN
        monitor.save(update_fields=['status'])

        timestamp = timezone.now().isoformat()
        alert_json = {
            "ALERT": f"Device {device_id} is down!",
            "time": timestamp
        }

        print("\n:::::::::::::::::::::Alert  message::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        print(f":::Message::::::\"Device {device_id} is down!\"::::::::::::::::::::::::::")
        print(f":::::::::::::::fields  ::{json.dumps(alert_json)}::::::::::::::::::::::::::::::")
        print(":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::\n")

        send_mail(
            subject=f"CRITICAL: Device {device_id} is Offline!",
            message=f"CritMon Alert: Device {device_id} failed to signal in time.",
            from_email="system@critmon.com",
            recipient_list=[monitor.alert_email],
            fail_silently=True,
        )

    except Monitor.DoesNotExist:
        pass
