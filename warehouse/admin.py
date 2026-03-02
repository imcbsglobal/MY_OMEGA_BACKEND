from django.contrib import admin
from .models import WarehouseTask


@admin.register(WarehouseTask)
class WarehouseTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'task_title', 'assigned_to', 'assigned_by',
        'assigned_date', 'due_date', 'total_work', 'completed_work',
        'status', 'created_at',
    ]
    list_filter = ['status', 'assigned_date', 'due_date']
    search_fields = ['task_title', 'assigned_to__username', 'assigned_by__username']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
