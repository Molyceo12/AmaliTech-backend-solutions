import json
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

def check_monitors():
    from .models import Monitor
    
    # Needs to be atomic if possible, but SQLite handles it sequentially.
    active_monitors = Monitor.objects.filter(status=Monitor.Status.ACTIVE)
    now = timezone.now()
    
    alerts = []
    
    for monitor in active_monitors:
        expiration_time = monitor.last_heartbeat + timedelta(seconds=monitor.timeout)
        if now >= expiration_time:
            # Trigger alert (Log critical error)
            alert_payload = {
                "ALERT": f"Device {monitor.id} is down!",
                "time": now.isoformat(),
                "alert_email": monitor.alert_email
            }
            # Console.log as requested by AC
            print("\n*** CRITICAL ALERT ***")
            print(json.dumps(alert_payload, indent=2))
            print("**********************\n")
            
            # Change status to DOWN
            monitor.status = Monitor.Status.DOWN
            monitor.save(update_fields=['status', 'last_heartbeat'])
            alerts.append(monitor.id)
            
            # Simulate sending an actual email using Django's Email Engine
            from django.core.mail import send_mail
            email_status = send_mail(
                subject=f"CRITICAL: Device {monitor.id} is Offline!",
                message=f"CritMon System Alert:\n\nThe tracking system lost contact with device '{monitor.id}'. It has been officially marked as DOWN.\nTime of failure: {now.isoformat()}",
                from_email="system@critmon.com",
                recipient_list=[monitor.alert_email],
                fail_silently=False,
            )
            
            if email_status:
                print(f"✅ SUCCESS: Alert email successfully virtually sent to {monitor.alert_email}")
            else:
                print(f"❌ FAILED: Could not send alert email to {monitor.alert_email}")
                
    return alerts
