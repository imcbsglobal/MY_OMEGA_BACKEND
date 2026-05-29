from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Payroll, PayrollDeduction, PayrollAllowance, AutomationRule

@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ['employee', 'month', 'year', 'gross_pay', 'net_pay', 'status']
    list_filter = ['status', 'month', 'year']
    search_fields = ['employee__name']

@admin.register(PayrollDeduction)
class PayrollDeductionAdmin(admin.ModelAdmin):
    list_display = ['payroll', 'deduction_type', 'amount']

@admin.register(PayrollAllowance)
class PayrollAllowanceAdmin(admin.ModelAdmin):
    list_display = ['payroll', 'allowance_type', 'amount']

@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    list_display = ['rule_name', 'rule_type', 'get_threshold', 'deduction_type', 'deduction_amount', 'is_active', 'created_at']
    list_filter = ['rule_type', 'is_active', 'deduction_type']
    search_fields = ['rule_name']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    def get_threshold(self, obj):
        """Display threshold in HH:MM format"""
        return obj.get_threshold_display()
    get_threshold.short_description = 'Threshold'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('rule_type', 'rule_name', 'is_active')
        }),
        ('Threshold Configuration', {
            'fields': ('threshold_hours', 'threshold_minutes')
        }),
        ('Deduction Configuration', {
            'fields': ('deduct_salary', 'deduction_type', 'deduction_amount')
        }),
        ('Additional Options', {
            'fields': ('deduct_half_day', 'deduct_full_day', 'set_occurrences', 'max_occurrences')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )