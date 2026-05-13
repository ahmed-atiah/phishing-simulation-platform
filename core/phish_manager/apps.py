from django.apps import AppConfig


class PhishManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'phish_manager'

    def ready(self):
        import os
        # Dev server: RUN_MAIN='true' → ana process, başlat
        # Gunicorn/Railway: RUN_MAIN set edilmez → DATABASE_URL varsa prodüksiyondayız, başlat
        # Hiçbiri değilse (dev server'ın reloader process'i) → atla
        run_main = os.environ.get('RUN_MAIN')
        in_production = os.environ.get('DATABASE_URL') is not None
        if run_main != 'true' and not in_production:
            return
        from .scheduler import start_scheduler
        start_scheduler()
