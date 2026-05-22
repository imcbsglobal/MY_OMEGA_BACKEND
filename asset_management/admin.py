from django.contrib import admin

from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('asset_name', 'asset_tag', 'category', 'employee', 'condition', 'status', 'assigned_date', 'return_date')
    list_filter = ('condition', 'status', 'category')
    search_fields = ('asset_name', 'asset_tag', 'serial_number', 'employee__full_name', 'employee__employee_id')
