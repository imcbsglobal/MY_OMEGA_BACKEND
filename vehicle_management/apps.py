# vehicle_management/apps.py
from django.apps import AppConfig


class VehicleManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vehicle_management'
    verbose_name = 'Vehicle & Travel Management'