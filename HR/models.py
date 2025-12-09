# HR/models.py - Updated Attendance Models with Punch In/Out Break System
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
    Model to store daily attendance records with multiple punch in/out
    Tracks first punch in and last punch out for the day
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
    
    # First Punch In (Start of Day)
    first_punch_in_time = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='First punch in timestamp (start of day)'
    )
    first_punch_in_location = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text='First punch in location'
    )
    first_punch_in_latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text='First punch in latitude'
    )
    first_punch_in_longitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text='First punch in longitude'
    )
    
    # Last Punch Out (End of Day)
    last_punch_out_time = models.DateTimeField(
        null=True, 
        blank=True,
        help_text='Last punch out timestamp (end of day)'
    )
    last_punch_out_location = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text='Last punch out location'
    )
    last_punch_out_latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text='Last punch out latitude'
    )
    last_punch_out_longitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        null=True, 
        blank=True,
        help_text='Last punch out longitude'
    )
    
    # Calculated Times
    total_working_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
        help_text='Total working hours (excluding breaks)'
    )
    total_break_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
        help_text='Total break hours'
    )
    
    # Current Status
    is_currently_on_break = models.BooleanField(
        default=False,
        help_text='Whether user is currently on break'
    )
    
    # Status and Verification
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='half',
        help_text='Attendance status'
    )
    verification_status = models.CharField(
        max_length=15, 
        choices=VERIFICATION_CHOICES, 
        default='unverified',
        help_text='Verification status by admin'
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
        ordering = ['-date', '-first_punch_in_time']
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['verification_status']),
        ]
    
    def __str__(self):
        return f"{self.user.name} - {self.date} - {self.get_status_display()}"
    
    def calculate_times(self):
        """Calculate total working hours and break hours from punch records"""
        punches = self.punch_records.all().order_by('punch_time')
        
        if not punches.exists():
            self.total_working_hours = 0
            self.total_break_hours = 0
            return
        
        total_work_seconds = 0
        total_break_seconds = 0
        last_in = None
        
        for punch in punches:
            if punch.punch_type == 'in':
                last_in = punch.punch_time
            elif punch.punch_type == 'out' and last_in:
                # Calculate duration between punch in and punch out
                duration = (punch.punch_time - last_in).total_seconds()
                
                # Determine if this is work time or break time
                # First in-out pair is work, subsequent pairs are breaks
                if not total_work_seconds:
                    total_work_seconds += duration
                else:
                    total_break_seconds += duration
                
                last_in = None
        
        self.total_working_hours = round(total_work_seconds / 3600, 2)
        self.total_break_hours = round(total_break_seconds / 3600, 2)
        
        # Update first and last punch times
        first_punch = punches.filter(punch_type='in').first()
        last_punch = punches.filter(punch_type='out').last()
        
        if first_punch:
            self.first_punch_in_time = first_punch.punch_time
            self.first_punch_in_location = first_punch.location
            self.first_punch_in_latitude = first_punch.latitude
            self.first_punch_in_longitude = first_punch.longitude
        
        if last_punch:
            self.last_punch_out_time = last_punch.punch_time
            self.last_punch_out_location = last_punch.location
            self.last_punch_out_latitude = last_punch.latitude
            self.last_punch_out_longitude = last_punch.longitude
            self.is_currently_on_break = False
        else:
            # If last punch is IN, user is currently on break
            last_punch_any = punches.last()
            if last_punch_any and last_punch_any.punch_type == 'in':
                self.is_currently_on_break = True
    
    def update_status(self):
        """Update attendance status based on working hours"""
        if self.total_working_hours >= 7.5:
            self.status = 'full'
        elif self.total_working_hours >= 4:
            self.status = 'half'
        else:
            self.status = 'half'
    
    @property
    def working_hours(self):
        """Backward compatibility property"""
        return self.total_working_hours
    
    @property
    def punch_in_time(self):
        """Backward compatibility property"""
        return self.first_punch_in_time
    
    @property
    def punch_out_time(self):
        """Backward compatibility property"""
        return self.last_punch_out_time
    
    @property
    def punch_in_location(self):
        """Backward compatibility property"""
        return self.first_punch_in_location
    
    @property
    def punch_out_location(self):
        """Backward compatibility property"""
        return self.last_punch_out_location


class PunchRecord(models.Model):
    """
    Model to store individual punch in/out records
    Each punch (in or out) creates a new record
    """
    PUNCH_TYPE_CHOICES = [
        ('in', 'Punch In'),
        ('out', 'Punch Out'),
    ]
    
    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.CASCADE,
        related_name='punch_records',
        help_text='Related attendance record'
    )
    punch_type = models.CharField(
        max_length=3,
        choices=PUNCH_TYPE_CHOICES,
        help_text='Type of punch (in/out)'
    )
    punch_time = models.DateTimeField(
        help_text='Punch timestamp'
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Punch location'
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text='GPS latitude'
    )
    longitude = models.DecimalField(
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text='GPS longitude'
    )
    note = models.TextField(
        blank=True,
        null=True,
        help_text='Note for this punch'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'hr_punch_record'
        verbose_name = 'Punch Record'
        verbose_name_plural = 'Punch Records'
        ordering = ['punch_time']
        indexes = [
            models.Index(fields=['attendance', 'punch_time']),
        ]
    
    def __str__(self):
        return f"{self.attendance.user.name} - {self.get_punch_type_display()} - {self.punch_time}"


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
        validators=[MinValueValidator(1), MaxValueValidator(240)]
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
    
    def __str__(self):
        try:
            user_name = self.user.name if hasattr(self.user, 'name') else str(self.user)
            return f"{user_name} - Late by {self.late_by_minutes} mins on {self.date}"
        except:
            return f"Late Request {self.id}"
    
    @property
    def late_time_display(self):
        """Display late time in hours and minutes"""
        try:
            hours = self.late_by_minutes // 60
            minutes = self.late_by_minutes % 60
            if hours > 0:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"
        except:
            return "Unknown"


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
        validators=[MinValueValidator(1), MaxValueValidator(240)]
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