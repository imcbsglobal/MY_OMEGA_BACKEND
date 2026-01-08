from django.db import models
from django.conf import settings
from cv_management.models import UserCvData


class OfferLetter(models.Model):
    STATUS_CHOICES = [
        ('willing', 'Willing'),
        ('not_willing', 'Not Willing'),
        ('sent', 'Sent'),
        ('draft', 'Draft')
    ]

    candidate = models.OneToOneField(
        UserCvData,
        on_delete=models.CASCADE,
        related_name='offer_letter',
        limit_choices_to={'interview_status': 'selected'}
    )

    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    department_id = models.CharField(max_length=100, null=True, blank=True)
    job_title_id = models.CharField(max_length=100, null=True, blank=True)
    
    # Total salary
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Salary breakdown components - REMOVED default=0 to allow proper saving
    basic_pay = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dearness_allowance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    house_rent_allowance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    special_allowance = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    conveyance_earnings = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    joining_data = models.DateField()
    notice_period = models.IntegerField()

    subject = models.CharField(max_length=255, default="Job Offer Letter")
    body = models.TextField()
    terms_condition = models.TextField(blank=True)
    
    pdf_file = models.FileField(upload_to='offer_letters/', null=True, blank=True)

    candidate_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    rejection_status = models.TextField(blank=True)
    
    work_start_time = models.TimeField(null=True, blank=True)
    work_end_time = models.TimeField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Offer Letter for {self.candidate.name} - {self.position}"
        
    def save(self, *args, **kwargs):
        """
        IMPORTANT: Removed automatic position setting
        Let the serializer/view handle all field values
        """
        print("=" * 80)
        print("MODEL SAVE METHOD CALLED")
        print("=" * 80)
        print(f"Salary breakdown BEFORE save:")
        print(f"  basic_pay: {self.basic_pay}")
        print(f"  dearness_allowance: {self.dearness_allowance}")
        print(f"  house_rent_allowance: {self.house_rent_allowance}")
        print(f"  special_allowance: {self.special_allowance}")
        print(f"  conveyance_earnings: {self.conveyance_earnings}")
        print(f"  salary: {self.salary}")
        print("=" * 80)
        
        # Just save without modifying anything
        super().save(*args, **kwargs)
        
        print("=" * 80)
        print("MODEL SAVED SUCCESSFULLY")
        print(f"Salary breakdown AFTER save:")
        print(f"  basic_pay: {self.basic_pay}")
        print(f"  dearness_allowance: {self.dearness_allowance}")
        print(f"  house_rent_allowance: {self.house_rent_allowance}")
        print(f"  special_allowance: {self.special_allowance}")
        print(f"  conveyance_earnings: {self.conveyance_earnings}")
        print(f"  salary: {self.salary}")
        print("=" * 80)