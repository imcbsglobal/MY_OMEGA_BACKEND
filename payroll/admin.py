from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Payroll, PayrollDeduction, PayrollAllowance

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