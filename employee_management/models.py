# employee_management/models.py - COMPLETE WITH PHONE NUMBER
from django.db import models
from django.conf import settings
from django.utils import timezone

class Employee(models.Model):
    """
    Employee model - extends AppUser with employment-specific information
    Links to your User.AppUser model
    """
    
    # Link to AppUser
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_profile'
    )

    # Basic Employee Information
    employee_id = models.CharField(
        max_length=64, 
        unique=True, 
        null=True, 
        blank=True,
        help_text='Employee ID (defaults to User ID, can be customized)',
        verbose_name='Employee ID'
    )
    
    # NEW: Employee Phone Number for WhatsApp notifications
    phone_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text='Employee contact number (WhatsApp enabled)',
        verbose_name='Phone Number'
    )
    
    # Employee Avatar/Photo
    avatar = models.ImageField(
        upload_to='employees/avatars/',
        null=True,
        blank=True,
        help_text='Employee photo/avatar'
    )
    
    # Employment Details
    employment_status = models.CharField(
        max_length=64, 
        null=True, 
        blank=True,
        help_text='E.g., Permanent, Contract, Probation'
    )
    employment_type = models.CharField(
        max_length=64, 
        null=True, 
        blank=True,
        help_text='E.g., Full-time, Part-time, Intern'
    )
    department = models.CharField(
        max_length=128, 
        null=True, 
        blank=True,
        help_text='Department name'
    )
    designation = models.CharField(
        max_length=128, 
        null=True, 
        blank=True,
        help_text='Job designation/title'
    )
    reporting_manager = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='subordinates',
        help_text='Direct reporting manager'
    )

    # Important Dates
    date_of_joining = models.DateField(null=True, blank=True)
    date_of_leaving = models.DateField(null=True, blank=True)
    probation_end_date = models.DateField(null=True, blank=True)
    confirmation_date = models.DateField(null=True, blank=True)

    # Salary Information
    basic_salary = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    allowances = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    gross_salary = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True
    )

    # Government IDs
    pf_number = models.CharField(
        max_length=64, 
        null=True, 
        blank=True,
        verbose_name='PF Number'
    )
    esi_number = models.CharField(
        max_length=64, 
        null=True, 
        blank=True,
        verbose_name='ESI Number'
    )
    pan_number = models.CharField(
        max_length=64, 
        null=True, 
        blank=True,
        verbose_name='PAN Number'
    )
    aadhar_number = models.CharField(
        max_length=12, 
        null=True, 
        blank=True,
        verbose_name='Aadhar Number',
        help_text='12-digit Aadhar number'
    )

    # Employee Location and Work Details
    location = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text='Employee location/place (e.g., City, State, Country)',
        verbose_name='Employee Location'
    )
    work_location = models.CharField(
        max_length=255, 
        null=True, 
        blank=True,
        help_text='Work office/branch location (optional)',
        verbose_name='Work Location'
    )
    duty_time = models.CharField(
        max_length=128, 
        null=True, 
        blank=True,
        help_text='E.g., 9:00 AM - 6:00 PM'
    )

    # Bank Details
    account_holder_name = models.CharField(max_length=128, null=True, blank=True)
    salary_account_number = models.CharField(max_length=64, null=True, blank=True)
    salary_bank_name = models.CharField(max_length=128, null=True, blank=True)
    salary_ifsc_code = models.CharField(max_length=32, null=True, blank=True)
    salary_branch = models.CharField(max_length=128, null=True, blank=True)

    # Document Attachments
    pan_card_attachment = models.FileField(
        upload_to='employees/pan/', 
        null=True, 
        blank=True
    )
    offer_letter = models.FileField(
        upload_to='employees/offer_letters/', 
        null=True, 
        blank=True
    )
    joining_letter = models.FileField(
        upload_to='employees/joining_letters/', 
        null=True, 
        blank=True
    )
    id_card_attachment = models.FileField(
        upload_to='employees/id_cards/', 
        null=True, 
        blank=True
    )

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=128, null=True, blank=True)
    emergency_contact_phone = models.CharField(max_length=32, null=True, blank=True)
    emergency_contact_relation = models.CharField(max_length=64, null=True, blank=True)

    # Personal Information
    blood_group = models.CharField(max_length=8, null=True, blank=True)
    marital_status = models.CharField(max_length=32, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)

    # Audit Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_employees'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee_management_employee'
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee_id or 'N/A'} - {self.get_full_name()}"
    
    def get_full_name(self):
        """Get full name from related user"""
        if self.user:
            if hasattr(self.user, 'name') and self.user.name:
                return self.user.name
            if hasattr(self.user, 'get_full_name') and callable(self.user.get_full_name):
                name = self.user.get_full_name()
                if name:
                    return name
            if hasattr(self.user, 'email'):
                return self.user.email
        return self.employee_id or 'Unknown'
    
    @property
    def full_name(self):
        """Property version of get_full_name for compatibility"""
        return self.get_full_name()
    
    def save(self, *args, **kwargs):
        """Auto-populate employee_id with user email if not provided"""
        if self.user and not self.employee_id:
            self.employee_id = self.user.email
        super().save(*args, **kwargs)


class EmployeeDocument(models.Model):
    """
    Additional documents related to an employee
    """
    employee = models.ForeignKey(
        Employee,
        related_name='additional_documents',
        on_delete=models.CASCADE
    )
    document_type = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text='Type of document (e.g., Certificate, License)'
    )
    title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='Document title'
    )
    document_file = models.FileField(upload_to='employees/documents/')
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'employee_management_employeedocument'
        verbose_name = 'Employee Document'
        verbose_name_plural = 'Employee Documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} - {self.employee.get_full_name()}"