# HR/models.py - Complete Attendance Management Models
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from User.models import AppUser


class Holiday(models.Model):
    """
    Model to store company holidays
    """
    name = models.CharField(max_length=200, help_text='Holiday name')
    date = models.DateField(unique=True, help_text='Holiday date')
    description = models.TextField(blank=True, null=True, help_text='Holiday description')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_holiday'
        verbose_name = 'Holiday'
        verbose_name_plural = 'Holidays'
        ordering = ['date']
    
    def __str__(self):
        return f"{self.name} - {self.date}"


class Attendance(models.Model):
    """
    Model to store daily attendance records with punch in/out
    """
    STATUS_CHOICES = [
        ('full', 'Full Day'),
        ('half', 'Half Day'),
        ('leave', 'Leave'),
        ('wfh', 'Work From Home'),
    ]
    
    VERIFICATION_CHOICES = [
        ('unverified', 'Unverified'),
        ('verified', 'Verified'),
    ]
    
    user = models.ForeignKey(
        AppUser, 
        on_delete=models.CASCADE, 
        related_name='attendances',
        help_text='User/Employee'
    )
    date = models.DateField(
        default=timezone.now,
        help_text='Attendance date'
    )
    
    # Punch In/Out Details
    punch_in_time = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='Punch in timestamp'
    )
    punch_out_time = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='Punch out timestamp'
    )
    punch_in_location = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text='Punch in location name'
    )
    punch_out_location = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text='Punch out location name'
    )
    punch_in_latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text='Punch in latitude'
    )
    punch_in_longitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text='Punch in longitude'
    )
    punch_out_latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text='Punch out latitude'
    )
    punch_out_longitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text='Punch out longitude'
    )
    
    # Status and Verification
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='full',
        help_text='Attendance status'
    )
    verification_status = models.CharField(
        max_length=15, 
        choices=VERIFICATION_CHOICES, 
        default='unverified',
        help_text='Verification status by admin'
    )
    
    # Working Hours
    working_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
        help_text='Total working hours'
    )
    
    # Notes
    note = models.TextField(
        blank=True, 
        null=True,
        help_text='Employee note'
    )
    admin_note = models.TextField(
        blank=True, 
        null=True,
        help_text='Admin/HR note'
    )
    
    # Admin actions
    verified_by = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_attendances',
        help_text='Admin who verified the attendance'
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Verification timestamp'
    )
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_attendance'
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'
        ordering = ['-date', '-punch_in_time']
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['verification_status']),
        ]
    
    def __str__(self):
        return f"{self.user.name} - {self.date} - {self.get_status_display()}"
    
    def calculate_working_hours(self):
        """Calculate working hours based on punch in/out times"""
        if self.punch_in_time and self.punch_out_time:
            delta = self.punch_out_time - self.punch_in_time
            hours = delta.total_seconds() / 3600
            self.working_hours = round(hours, 2)
        return self.working_hours
    
    def save(self, *args, **kwargs):
        """Override save to auto-calculate working hours"""
        if self.punch_in_time and self.punch_out_time:
            self.calculate_working_hours()
        super().save(*args, **kwargs)


class LeaveRequest(models.Model):
    """
    Model to store leave requests from employees
    """
    LEAVE_TYPE_CHOICES = [
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
        ('earned', 'Earned Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('emergency', 'Emergency Leave'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='leave_requests',
        help_text='User requesting leave'
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPE_CHOICES,
        help_text='Type of leave'
    )
    from_date = models.DateField(help_text='Leave start date')
    to_date = models.DateField(help_text='Leave end date')
    reason = models.TextField(help_text='Reason for leave')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Leave request status'
    )
    
    # Admin response
    reviewed_by = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_leaves',
        help_text='Admin who reviewed the request'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_comment = models.TextField(blank=True, null=True)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_leave_request'
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.leave_type} - {self.from_date} to {self.to_date}"
    
    @property
    def total_days(self):
        """Calculate total days of leave"""
        delta = self.to_date - self.from_date
        return delta.days + 1
    




class Break(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='breaks')
    break_start = models.DateTimeField()
    break_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)    




# Add these models to your HR/models.py file

class LateRequest(models.Model):
    """
    Model to store late arrival requests from employees
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='late_requests',
        help_text='User requesting late arrival'
    )
    date = models.DateField(help_text='Date of late arrival')
    late_by_minutes = models.IntegerField(
        help_text='How many minutes late',
        validators=[MinValueValidator(1), MaxValueValidator(240)]  # Max 4 hours
    )
    reason = models.TextField(help_text='Reason for late arrival')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Request status'
    )
    
    # Admin response
    reviewed_by = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_late_requests',
        help_text='Admin who reviewed the request'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_comment = models.TextField(blank=True, null=True)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_late_request'
        verbose_name = 'Late Request'
        verbose_name_plural = 'Late Requests'
        ordering = ['-created_at']
        unique_together = ['user', 'date']
    
    def __str__(self):
        return f"{self.user.name} - Late by {self.late_by_minutes} mins on {self.date}"
    
    @property
    def late_time_display(self):
        """Display late time in hours and minutes"""
        hours = self.late_by_minutes // 60
        minutes = self.late_by_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


class EarlyRequest(models.Model):
    """
    Model to store early departure requests from employees
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='early_requests',
        help_text='User requesting early departure'
    )
    date = models.DateField(help_text='Date of early departure')
    early_by_minutes = models.IntegerField(
        help_text='How many minutes early',
        validators=[MinValueValidator(1), MaxValueValidator(240)]  # Max 4 hours
    )
    reason = models.TextField(help_text='Reason for early departure')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Request status'
    )
    
    # Admin response
    reviewed_by = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_early_requests',
        help_text='Admin who reviewed the request'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_comment = models.TextField(blank=True, null=True)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_early_request'
        verbose_name = 'Early Request'
        verbose_name_plural = 'Early Requests'
        ordering = ['-created_at']
        unique_together = ['user', 'date']
    
    def __str__(self):
        return f"{self.user.name} - Early by {self.early_by_minutes} mins on {self.date}"
    
    @property
    def early_time_display(self):
        """Display early time in hours and minutes"""
        hours = self.early_by_minutes // 60
        minutes = self.early_by_minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"




    
# HR/models.py (add near other models)
from django.db import models
from django.utils import timezone
from User.models import AppUser  # already present in your file

class AttendanceBreak(models.Model):
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='breaks')
    attendance = models.ForeignKey('Attendance', on_delete=models.CASCADE, related_name='attendance_breaks')

    break_start = models.DateTimeField()
    break_end = models.DateTimeField(null=True, blank=True)

    duration_minutes = models.IntegerField(null=True, blank=True)
    duration_display = models.CharField(max_length=32, null=True, blank=True)

    note = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hr_attendance_break'
        ordering = ['-break_start']

    def calculate_duration(self):
        if self.break_start and self.break_end:
            seconds = (self.break_end - self.break_start).total_seconds()
            mins = int(seconds // 60)
            self.duration_minutes = mins
            hours = mins // 60
            mins_r = mins % 60
            self.duration_display = f"{hours}h {mins_r}m" if hours else f"{mins_r}m"
            return self.duration_minutes
        return None

    def save(self, *args, **kwargs):
        if self.break_start and self.break_end:
            self.calculate_duration()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"AttendanceBreak {self.id} - {self.user} - {self.break_start:%Y-%m-%d %H:%M}"

    