from django.contrib import admin
from .models import WarehouseTask


@admin.register(WarehouseTask)
class WarehouseTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'task_title', 'assigned_to', 'assigned_by',
        'assigned_date', 'due_date', 'total_work', 'completed_work',
        'status', 'start_datetime', 'completed_datetime', 'duration_display_admin', 'created_at',
    ]
    list_filter = ['status', 'assigned_date', 'due_date', 'created_at']
    search_fields = ['task_title', 'assigned_to__username', 'assigned_by__username']
    readonly_fields = ['created_at', 'updated_at', 'start_datetime', 'completed_datetime', 'duration_display_admin', 'duration_hours']
    fieldsets = (
        ('Task Information', {
            'fields': ('task_title', 'description', 'status')
        }),
        ('Assignment', {
            'fields': ('assigned_by', 'assigned_to', 'assigned_date', 'due_date')
        }),
        ('Work Progress', {
            'fields': ('total_work', 'completed_work')
        }),
        ('Timeline & Duration', {
            'fields': ('start_datetime', 'completed_datetime', 'duration_display_admin', 'duration_hours')
        }),
        ('Additional', {
            'fields': ('remarks', 'created_at', 'updated_at')
        }),
    )
    ordering = ['-created_at']

    def duration_display_admin(self, obj):
        return obj.duration_display
    duration_display_admin.short_description = "Duration"
