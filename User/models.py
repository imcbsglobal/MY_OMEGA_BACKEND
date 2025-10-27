from django.db import models
from django.core.validators import RegexValidator

class AppUser(models.Model):
    class Levels(models.TextChoices):
        SUPER_ADMIN = 'Super Admin', 'Super Admin'
        ADMIN = 'Admin', 'Admin'
        USER = 'User', 'User'

    photo = models.ImageField(upload_to='users/photos/', blank=True, null=True)  # optional
    name = models.CharField(max_length=150)
    email = models.EmailField(max_length=255, unique=True)  # Email is the user ID
    password = models.CharField(max_length=128)  # will store a hashed value
    user_level = models.CharField(max_length=20, choices=Levels.choices, default=Levels.USER)
    job_role = models.CharField(max_length=100, blank=True)   # optional
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r'^\+?\d{7,15}$', 'Enter a valid phone number.')]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"
