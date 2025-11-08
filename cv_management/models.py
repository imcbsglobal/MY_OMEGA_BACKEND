from django.db import models
from User.models import AppUser
import uuid


class JobTitle(models.Model):
    """Job Title model with UUID for secure access"""
    title = models.CharField(max_length=100,unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    class Meta:
        db_table = "job_titles"
        verbose_name_plural = "Job Titles"


class UserCvData(models.Model):
    """Model to store candidate CV and related information."""

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    INTERVIEW_STATUS_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
        ('pending', 'Pending'),
    ]

    KERALA_DISTRICTS = [
        ('Alappuzha', 'Alappuzha'),
        ('Ernakulam', 'Ernakulam'),
        ('Idukki', 'Idukki'),
        ('Kannur', 'Kannur'),
        ('Kasaragod', 'Kasaragod'),
        ('Kollam', 'Kollam'),
        ('Kottayam', 'Kottayam'),
        ('Kozhikode', 'Kozhikode'),
        ('Malappuram', 'Malappuram'),
        ('Palakkad', 'Palakkad'),
        ('Pathanamthitta', 'Pathanamthitta'),
        ('Thiruvananthapuram', 'Thiruvananthapuram'),
        ('Thrissur', 'Thrissur'),
        ('Wayanad', 'Wayanad'),
        ('Other', 'Other'),
    ]

    # uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    # Basic Info
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='O')
    dob = models.DateField(verbose_name="Date of Birth", null=True, blank=True)

    # Job Info
    job_title = models.ForeignKey(
        JobTitle, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='cv_data',
        verbose_name="Job Title"
    )
    place = models.CharField(max_length=100)
    district = models.CharField(max_length=100, choices=KERALA_DISTRICTS, default='Wayanad')
    education = models.CharField(max_length=100)
    experience = models.CharField(max_length=50, verbose_name="Experience (e.g. 5 years)")

    # Contact Info
    email = models.EmailField(unique=True, verbose_name="Email Address")
    phone_number = models.CharField(max_length=15, verbose_name="Phone Number")
    address = models.CharField(max_length=255, blank=True, null=True)

    # CV and Source
    cv_file = models.FileField(upload_to='cvs/', null=True, blank=True, verbose_name="CV File")
    cv_source = models.CharField(max_length=50, verbose_name="CV Source", default='Direct')
    interview_status = models.CharField(
        max_length=10,
        choices=INTERVIEW_STATUS_CHOICES,
        default='pending',
        verbose_name="Interview Status"
    )
    remarks = models.CharField(max_length=255, blank=True, null=True)

    # Meta Info
    created_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='created_cvs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        
        return f"{self.name} - {self.job_title}"
    
    class Meta:
        db_table = "user_cv_data"
        verbose_name_plural = "User CV Data"
