from django.db import models
from cv_management.models import UserCvData
from User.models import AppUser
import uuid

class InterviewManagement(models.Model):
    """Stores detailed interview evaluation and results."""

    RESULT_CHOICES =[
        ('SELECTED','selected'),
        ("REJECTED",'rejected'),
        ("PENDING",'pending')
    ]

    LANGUAGE_CHOICES = [
    ('English', 'English'),
    ('Malayalam', 'Malayalam'),
    ('Tamil', 'Tamil'),
    ('Hindi', 'Hindi'),
    ('Other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True,default=uuid.uuid4 ,editable=False)

    candidate = models.ForeignKey(
        UserCvData,
        on_delete=models.CASCADE,
        related_name='interviews',
        verbose_name='Candidate'
    )

    interview_date = models.DateTimeField()
    interviewer = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        null=True,
        related_name='interviews_conducted',
        verbose_name="Interviewer"
    )

