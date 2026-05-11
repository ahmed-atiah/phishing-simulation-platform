from django.apps import AppConfig


class PhishManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'phish_manager'

    def ready(self):
        # Sadece ana process'te başlat (reloader'ın ikinci process'ini engelle)
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            return
        from .scheduler import start_scheduler
        start_scheduler()
