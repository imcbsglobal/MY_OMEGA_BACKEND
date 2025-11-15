from django.db import models
from django.conf import settings
from cv_management.models import UserCvData


class OfferLetter(models.Model):
    STATUS_CHOICES = [
        ('willing', 'Willing'),
        ('not_willing', 'Not Willing'),
        ('sent','Sent'),
        ('draft','Draft')
    ]

    candidate = models.OneToOneField(
        UserCvData,
        on_delete=models.CASCADE,
        related_name='offer_letter',
        limit_choices_to={'interview_status':'selected'}
    )

    position = models.CharField(max_length=100)
    department= models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    joining_data = models.DateField()
    notice_period= models.IntegerField()

    subject = models.CharField(default="Job Offer Letter")  
    body = models.TextField()
    terms_condition = models.TextField(blank=True)
    
    pdf_file = models.FileField(upload_to='offer_letters/', null=True, blank=True)

    candidate_status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='draft')
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
            # Auto-set position from candidate's job title if not set
            if not self.position and self.candidate.job_title:
                self.position = self.candidate.job_title.title
            super().save(*args, **kwargs)