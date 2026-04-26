from django.db import models

class Monitor(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        DOWN = 'down', 'Down'
        PAUSED = 'paused', 'Paused'

    id = models.CharField(max_length=255, primary_key=True)
    timeout = models.IntegerField(help_text="Timeout in seconds")
    alert_email = models.EmailField()
    last_heartbeat = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    def __str__(self):
        return f"{self.id} - {self.status}"
