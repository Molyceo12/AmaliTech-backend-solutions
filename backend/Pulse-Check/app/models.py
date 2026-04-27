from django.db import models

class Monitor(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        DOWN = 'down', 'Down'
        PAUSED = 'paused', 'Paused'

    id = models.CharField(max_length=255, primary_key=True)
    timeout = models.IntegerField(default=60)
    alert_email = models.EmailField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    task_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.id} ({self.status})"
