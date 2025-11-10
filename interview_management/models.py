from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from cv_management.models import UserCvData
from User.models import AppUser
import uuid


class Interview(models.Model):
    """Stores scheduled interviews and results."""

    RESULT_CHOICES = [
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
        ('pending', 'Pending'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    candidate = models.ForeignKey(
        UserCvData,
        on_delete=models.CASCADE,
        related_name='interviews',
        verbose_name='Candidate'
    )

    interviewer = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interviews_conducted',
        verbose_name='Interviewer'
    )

    scheduled_at = models.DateTimeField(verbose_name="Scheduled Date & Time")
    status = models.CharField(max_length=10, choices=RESULT_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_at']
        verbose_name = "Interview"
        verbose_name_plural = "Interviews"

    def __str__(self):
        return f"Interview - {self.candidate} ({self.status})"


class InterviewEvaluation(models.Model):
    """Stores evaluation details and rating for an interview."""

    interview = models.OneToOneField(
        Interview,
        on_delete=models.CASCADE,
        related_name='evaluation'
    )

    appearance = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        null=True, blank=True, default=0
    )
    knowledge = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        null=True, blank=True, default=0
    )
    confidence = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        null=True, blank=True, default=0
    )
    attitude = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        null=True, blank=True, default=0
    )
    communication = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        null=True, blank=True, default=0
    )

    languages = models.CharField(max_length=255, blank=True, default='')
    expected_salary = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, help_text="Expected salary in local currency"
    )
    experience = models.TextField(blank=True, default='')
    remark = models.TextField(blank=True, default='')

    voice_note = models.FileField(
        upload_to='voice_notes/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp3', 'wav', 'm4a'])]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Interview Evaluation"
        verbose_name_plural = "Interview Evaluations"

    def __str__(self):
        return f"Evaluation for {self.interview.candidate}"

    @property
    def average_rating(self):
        """Compute the average score for numeric fields."""
        scores = [self.appearance, self.knowledge, self.confidence, self.attitude, self.communication]
        valid_scores = [s for s in scores if s is not None]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0
 