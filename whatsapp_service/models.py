from django.db import models

# Create your models here.
# whatsapp_service/models.py
from django.db import models
from django.core.validators import RegexValidator

class WhatsAppConfiguration(models.Model):
    """
    Stores WhatsApp API configuration
    Only one active configuration at a time
    """
    PROVIDER_CHOICES = [
        ('dxing', 'DXING'),
        ('twilio', 'Twilio'),
        ('meta', 'Meta Cloud API'),
    ]
    
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default='dxing',
        help_text="WhatsApp service provider"
    )
    api_url = models.URLField(
        max_length=500,
        default='https://app.dxing.in/api/send/whatsapp',
        help_text="API endpoint URL"
    )
    api_secret = models.CharField(
        max_length=500,
        help_text="API Secret Key"
    )
    account_id = models.CharField(
        max_length=500,
        help_text="Account ID"
    )
    default_priority = models.IntegerField(
        default=1,
        help_text="Default message priority (1-10)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Only one configuration can be active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "WhatsApp Configuration"
        verbose_name_plural = "WhatsApp Configurations"
    
    def save(self, *args, **kwargs):
        # Ensure only one active configuration
        if self.is_active:
            WhatsAppConfiguration.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.provider} - {'Active' if self.is_active else 'Inactive'}"


class AdminNumber(models.Model):
    """
    Stores admin/HR phone numbers for notifications
    """
    ROLE_CHOICES = [
        ('hr_admin', 'HR Admin'),
        ('manager', 'Manager'),
        ('payroll_admin', 'Payroll Admin'),
        ('global_cc', 'Global CC'),
    ]
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be in format: '+999999999'. Up to 15 digits allowed."
    )
    
    name = models.CharField(
        max_length=100,
        help_text="Admin name for reference"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        unique=True,
        help_text="Phone number with country code (e.g., +918281561081)"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text="Admin role for routing notifications"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Receive notifications"
    )
    is_api_sender = models.BooleanField(
        default=False,
        help_text="Mark as API sender number (will be excluded from notifications)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Admin Number"
        verbose_name_plural = "Admin Numbers"
        ordering = ['role', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_role_display()}) - {self.phone_number}"


class MessageTemplate(models.Model):
    """
    Stores message templates for different notification types
    """
    TEMPLATE_TYPE_CHOICES = [
        ('punch_in', 'Punch In'),
        ('punch_out', 'Punch Out'),
        ('leave_request', 'Leave Request'),
        ('leave_approval', 'Leave Approval'),
        ('leave_rejection', 'Leave Rejection'),
        ('late_request', 'Late Request'),
        ('late_approval', 'Late Approval'),
        ('late_rejection', 'Late Rejection'),
        ('early_request', 'Early Request'),
        ('early_approval', 'Early Approval'),
        ('early_rejection', 'Early Rejection'),
        ('generic_notification', 'Generic Notification'),
    ]
    
    RECIPIENT_TYPE_CHOICES = [
        ('employee', 'Employee'),
        ('admin', 'Admin/HR'),
        ('both', 'Both'),
    ]
    
    template_type = models.CharField(
        max_length=30,
        choices=TEMPLATE_TYPE_CHOICES,
        unique=True,
        help_text="Type of notification"
    )
    recipient_type = models.CharField(
        max_length=10,
        choices=RECIPIENT_TYPE_CHOICES,
        default='both',
        help_text="Who receives this template"
    )
    template_text = models.TextField(
        help_text="Message template. Available variables: {employee_name}, {action}, {date}, {time}, {location}, {reason}, {days}, {leave_type}, {status}, {approver_name}"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Use this template"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Message Template"
        verbose_name_plural = "Message Templates"
        ordering = ['template_type']
    
    def __str__(self):
        return f"{self.get_template_type_display()} - {self.get_recipient_type_display()}"
    
    def render(self, **context):
        """
        Render template with context variables
        """
        message = self.template_text
        for key, value in context.items():
            placeholder = "{" + key + "}"
            message = message.replace(placeholder, str(value))
        return message