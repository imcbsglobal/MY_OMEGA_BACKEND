# HR/admin.py
from django.contrib import admin
from .models import Attendance, Holiday, LeaveRequest, LateRequest, EarlyRequest


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'status', 'verification_status',
        'punch_in_time', 'punch_out_time', 'working_hours'
    ]
    list_filter = ['status', 'verification_status', 'date']
    search_fields = ['user__name', 'user__email']
    readonly_fields = ['working_hours', 'created_at', 'updated_at']
    date_hierarchy = 'date'

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'date', 'status', 'verification_status')
        }),
        ('Punch Details', {
            'fields': (
                'punch_in_time', 'punch_in_location', 'punch_in_latitude', 'punch_in_longitude',
                'punch_out_time', 'punch_out_location', 'punch_out_latitude', 'punch_out_longitude'
            )
        }),
        ('Working Hours', {
            'fields': ('working_hours',)
        }),
        ('Notes', {
            'fields': ('note', 'admin_note')
        }),
        ('Verification', {
            'fields': ('verified_by', 'verified_at')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'is_active', 'created_at']
    list_filter = ['is_active', 'date']
    search_fields = ['name', 'description']
    date_hierarchy = 'date'


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'leave_type', 'from_date', 'to_date',
        'status', 'total_days', 'created_at'
    ]
    list_filter = ['leave_type', 'status', 'from_date']
    search_fields = ['user__name', 'user__email', 'reason']
    readonly_fields = ['total_days', 'created_at', 'updated_at']
    date_hierarchy = 'from_date'

    fieldsets = (
        ('Leave Request', {
            'fields': ('user', 'leave_type', 'from_date', 'to_date', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_comment')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LateRequest)
class LateRequestAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'late_by_minutes', 'status', 'created_at'
    ]
    list_filter = ['status', 'date']
    search_fields = ['user__name', 'user__email', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'

    fieldsets = (
        ('Late Request', {
            'fields': ('user', 'date', 'late_by_minutes', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_comment')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EarlyRequest)
class EarlyRequestAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'early_by_minutes', 'status', 'created_at'
    ]
    list_filter = ['status', 'date']
    search_fields = ['user__name', 'user__email', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'

    fieldsets = (
        ('Early Request', {
            'fields': ('user', 'date', 'early_by_minutes', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_comment')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )





