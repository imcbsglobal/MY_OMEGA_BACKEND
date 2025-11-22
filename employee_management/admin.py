# employee_management/admin.py
from django.contrib import admin
from .models import Employee, EmployeeDocument


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'employee_id', 
        'get_full_name', 
        'designation', 
        'department', 
        'employment_status',
        'location',
        'is_active',
        'created_at'
    ]
    list_filter = [
        'is_active', 
        'employment_status', 
        'employment_type',
        'department',
        'created_at'
    ]
    search_fields = [
        'employee_id', 
        'user__email', 
        'user__name',
        'designation',
        'department',
        'location'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Link', {
            'fields': ('user', 'employee_id')
        }),
        ('Job Information', {
            'fields': (
                'employment_status', 
                'employment_type',
                'department',
                'designation',
                'reporting_manager',
                'date_of_joining',
                'date_of_leaving',
                'probation_end_date',
                'confirmation_date'
            )
        }),
        ('Location & Timing', {
            'fields': (
                'location',
                'work_location',
                'duty_time'
            )
        }),
        ('Salary Information', {
            'fields': (
                'basic_salary',
                'allowances',
                'gross_salary'
            )
        }),
        ('Government IDs', {
            'fields': (
                'pf_number',
                'esi_number',
                'pan_number',
                'aadhar_number'
            )
        }),
        ('Bank Details', {
            'fields': (
                'account_holder_name',
                'salary_account_number',
                'salary_bank_name',
                'salary_ifsc_code',
                'salary_branch'
            )
        }),
        ('Documents', {
            'fields': (
                'pan_card_attachment',
                'offer_letter',
                'joining_letter',
                'id_card_attachment'
            )
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name',
                'emergency_contact_phone',
                'emergency_contact_relation'
            )
        }),
        ('Personal Information', {
            'fields': (
                'blood_group',
                'marital_status',
                'notes'
            )
        }),
        ('Status & Audit', {
            'fields': (
                'is_active',
                'created_by',
                'created_at',
                'updated_at'
            )
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'employee',
        'document_type',
        'issue_date',
        'expiry_date',
        'uploaded_at'
    ]
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['title', 'employee__employee_id', 'employee__user__name']
    readonly_fields = ['uploaded_at']