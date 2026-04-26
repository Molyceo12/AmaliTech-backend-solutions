from django.apps import AppConfig
import os

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # We no longer need the APScheduler background polling.
        # The new Redis + Timer architecture is event-driven.
        pass
