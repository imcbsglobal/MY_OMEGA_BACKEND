from django.db import models
from User.models import AppUser


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
    # Basic Info
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='O')
    dob = models.DateField(verbose_name="Date of Birth", null=True, blank=True)

    # Job Info
    job_title = models.CharField(max_length=100, verbose_name="Job Title")
    place = models.CharField(max_length=100)
    district = models.CharField(max_length=100,choices=KERALA_DISTRICTS, default='Wayanad')
    education = models.CharField(max_length=100)
    experience = models.CharField(max_length=50, verbose_name="Experience (e.g. 5 years)")

    # Contact Info
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
    created_user = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='created_cvs')
    updated_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, related_name='updated_cvs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.job_title}"

class JobTitle(models.Model):
    title = models.CharField(max_length=100)
    createdAt= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    