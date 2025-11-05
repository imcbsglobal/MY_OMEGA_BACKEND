# User/models.py - COMPLETE VERSION WITH EMPLOYEE FIELDS
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class AppUserManager(BaseUserManager):
    """Custom manager for AppUser"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_level', 'Super Admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


class AppUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with employee information
    Combines authentication and HR employee data
    """
    USER_LEVEL_CHOICES = [
        ('Super Admin', 'Super Admin'),
        ('Admin', 'Admin'),
        ('User', 'User'),
    ]
    
    # ========== AUTHENTICATION FIELDS ==========
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # Inherited but explicit
    
    # ========== PERSONAL INFORMATION ==========
    name = models.CharField(max_length=255, help_text='Full name')
    dob = models.DateField(
        null=True, 
        blank=True, 
        verbose_name='Date of Birth',
        help_text='Date of birth'
    )
    photo = models.ImageField(
        upload_to='user_photos/',
        null=True,
        blank=True,
        help_text='User profile photo'
    )
    
    # ========== CONTACT INFORMATION ==========
    address = models.TextField(
        blank=True, 
        null=True,
        help_text='Full residential address'
    )
    place = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text='Place/City'
    )
    district = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text='District'
    )
    personal_phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name='Personal Phone',
        help_text='Personal contact number'
    )
    residential_phone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name='Residential Phone',
        help_text='Residential contact number'
    )
    phone_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text='Primary phone number (legacy field)'
    )
    
    # ========== PROFESSIONAL INFORMATION ==========
    user_level = models.CharField(
        max_length=20, 
        choices=USER_LEVEL_CHOICES, 
        default='User',
        help_text='System access level'
    )
    job_title = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text='Job title/position'
    )
    job_role = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text='Job role (alternative to job_title)'
    )
    organization = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text='Organization/Department'
    )
    education = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text='Educational qualification'
    )
    experience = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text='Years of experience'
    )
    joining_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date of joining organization'
    )
    duty_time_start = models.TimeField(
        null=True, 
        blank=True,
        verbose_name='Duty Start Time',
        help_text='Daily duty start time'
    )
    duty_time_end = models.TimeField(
        null=True, 
        blank=True,
        verbose_name='Duty End Time',
        help_text='Daily duty end time'
    )
    
    # ========== FINANCIAL INFORMATION ==========
    bank_account_number = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text='Bank account number'
    )
    ifsc_code = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name='IFSC Code',
        help_text='Bank IFSC code'
    )
    bank_name = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text='Bank name'
    )
    branch = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text='Bank branch'
    )
    
    # ========== DOCUMENTS ==========
    aadhar_attachment = models.FileField(
        upload_to='user_documents/aadhar/',
        null=True,
        blank=True,
        verbose_name='Aadhar Card',
        help_text='Aadhar card document'
    )
    
    # ========== SYSTEM FIELDS ==========
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    # Fix the groups and permissions many-to-many relationships
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='appuser_set',
        related_query_name='appuser',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='appuser_set',
        related_query_name='appuser',
    )
    
    objects = AppUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    class Meta:
        db_table = 'user_appuser'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    @property
    def username(self):
        """Compatibility property for systems expecting username"""
        return self.email
    
    @property
    def first_name(self):
        """Extract first name from name field"""
        return self.name.split()[0] if self.name else ''
    
    @property
    def last_name(self):
        """Extract last name from name field"""
        parts = self.name.split()
        return ' '.join(parts[1:]) if len(parts) > 1 else ''
    
    def get_full_name(self):
        return self.name
    
    def get_short_name(self):
        return self.name.split()[0] if self.name else self.email
    
    def get_job_title_display(self):
        """Return job_title if available, otherwise job_role"""
        return self.job_title or self.job_role or 'N/A'