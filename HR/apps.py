# HR/apps.py
from django.apps import AppConfig


class HRConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "HR"

    def ready(self):
        # Import signals so Django registers them
        try:
            import HR.signals  # noqa: F401
        except Exception as e:
            # If this blows up, you'll see it in the console
            print("Error importing HR.signals:", e)
