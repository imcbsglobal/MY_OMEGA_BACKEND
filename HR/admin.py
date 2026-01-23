# HR/admin.py - Complete Clean Admin Configuration
from django.contrib import admin
from .models import Attendance, Holiday, LeaveRequest, LateRequest, EarlyRequest, PunchRecord


class PunchRecordInline(admin.TabularInline):
    """Inline admin for punch records"""
    model = PunchRecord
    extra = 0
    readonly_fields = ['punch_time', 'created_at']
    fields = ['punch_type', 'punch_time', 'location', 'latitude', 'longitude', 'note']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'status', 'verification_status',
        'first_punch_in_time', 'last_punch_out_time', 
        'total_working_hours', 'total_break_hours', 'is_currently_on_break'
    ]
    list_filter = ['status', 'verification_status', 'date', 'is_currently_on_break']
    search_fields = ['user__name', 'user__email']
    readonly_fields = ['total_working_hours', 'total_break_hours', 'is_currently_on_break', 'created_at', 'updated_at']
    date_hierarchy = 'date'
    inlines = [PunchRecordInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'date', 'status', 'verification_status')
        }),
        ('First Punch In Details', {
            'fields': (
                'first_punch_in_time', 'first_punch_in_location', 
                'first_punch_in_latitude', 'first_punch_in_longitude'
            )
        }),
        ('Last Punch Out Details', {
            'fields': (
                'last_punch_out_time', 'last_punch_out_location', 
                'last_punch_out_latitude', 'last_punch_out_longitude'
            )
        }),
        ('Calculated Times', {
            'fields': ('total_working_hours', 'total_break_hours', 'is_currently_on_break')
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


@admin.register(PunchRecord)
class PunchRecordAdmin(admin.ModelAdmin):
    list_display = ['attendance', 'punch_type', 'punch_time', 'location']
    list_filter = ['punch_type', 'punch_time']
    search_fields = ['attendance__user__name', 'attendance__user__email', 'location']
    readonly_fields = ['created_at']
    date_hierarchy = 'punch_time'
    
    fieldsets = (
        ('Punch Information', {
            'fields': ('attendance', 'punch_type', 'punch_time')
        }),
        ('Location Details', {
            'fields': ('location', 'latitude', 'longitude')
        }),
        ('Additional Info', {
            'fields': ('note', 'created_at')
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
        'user', 'leave_master', 'from_date', 'to_date',
        'status', 'total_days', 'created_at'
    ]
    list_filter = ['status', 'from_date']  # You can filter by category through leave_master
    search_fields = ['user__name', 'user__email', 'reason', 'leave_master__leave_name']
    readonly_fields = ['total_days', 'created_at', 'updated_at', 'is_paid']
    date_hierarchy = 'from_date'

    fieldsets = (
        ('Leave Request', {
            'fields': ('user', 'leave_master', 'from_date', 'to_date', 'reason')
        }),
        ('Leave Details', {
            'fields': ('is_paid', 'deducted_from_balance')
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