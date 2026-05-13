from django.apps import AppConfig


class PhishManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'phish_manager'

    def ready(self):
        import os, sys
        if 'test' in sys.argv:
            return
        run_main = os.environ.get('RUN_MAIN')
        # Dev server inner process, Railway (DATABASE_URL), veya PythonAnywhere (SCHEDULER_ENABLED)
        in_production = (
            os.environ.get('DATABASE_URL') is not None or
            os.environ.get('SCHEDULER_ENABLED', '').lower() == 'true'
        )
        if run_main != 'true' and not in_production:
            return
        from .scheduler import start_scheduler
        start_scheduler()
