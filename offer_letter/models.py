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

    cadidate = models.OneToOneField(
        UserCvData,
        on_delete=models.CASCADE,
        related_name='offer_letter',
        limit_choices_to={'interview_status':'selected'}
    )

    position = models.CharField(max_length=100)
    salary = models.DecimalField(max_length=10,decimal_places=2)
    joining_data = models.DateField()
    notice_period= models.IntegerField()

    subject = models.CharField(max_length=200,default="Job Offer Letter")  
    body = models.TextField()
    terms_condition = models.TextField(blank=True)
    
    pdf_file = models.FileField(upload_to='offer_letters/', null=True, blank=True)

    candidate_status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='draft')
    rejection_status = models.TextField(blank=True)

    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']