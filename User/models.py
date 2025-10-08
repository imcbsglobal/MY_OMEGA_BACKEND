from django.db import models
from django.core.validators import RegexValidator

class AppUser(models.Model):
    class Levels(models.TextChoices):
        SUPER_ADMIN = 'Super Admin', 'Super Admin'
        ADMIN = 'Admin', 'Admin'
        USER = 'User', 'User'

    photo = models.ImageField(upload_to='users/photos/')
    name = models.CharField(max_length=150)
    user_id = models.CharField(max_length=64, unique=True)  # “don’t work same user id”
    password = models.CharField(max_length=128)  # will store a hashed value
    user_level = models.CharField(max_length=20, choices=Levels.choices)
    job_role = models.CharField(max_length=100)
    phone_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?\d{7,15}$', 'Enter a valid phone number.')]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.user_id})"
