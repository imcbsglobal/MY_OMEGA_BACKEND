# delivery_management/apps.py
from django.apps import AppConfig


class DeliveryManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'delivery_management'
    verbose_name = 'Delivery Management'
    
    def ready(self):
        """
        Import signals or perform other startup tasks here
        """
        pass
        # Example: import signals
        # import delivery_management.signals