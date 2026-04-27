from pulse_check.celery import app as celery_app
from .models import Monitor

def start_monitor_timer(device_id, timeout_seconds):
    cancel_monitor_timer(device_id)
    
    from .tasks import trigger_alert_task
    task = trigger_alert_task.apply_async(
        args=[device_id],
        countdown=timeout_seconds
    )
    
    Monitor.objects.filter(id=device_id).update(task_id=task.id)

def cancel_monitor_timer(device_id):
    monitor = Monitor.objects.filter(id=device_id).first()
    if monitor and monitor.task_id:
        celery_app.control.revoke(monitor.task_id, terminate=True)
        Monitor.objects.filter(id=device_id).update(task_id=None)
