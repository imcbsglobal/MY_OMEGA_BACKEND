# HR/models.py - FIXED VERSION

from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from User.models import AppUser
from decimal import Decimal


class Holiday(models.Model):
    """Model to store company holidays"""
    HOLIDAY_TYPE_CHOICES = [
        ('mandatory', 'Mandatory Holiday (Paid)'),
        ('special', 'Special Holiday (Paid)'),
        ('optional', 'Optional Holiday'),
    ]
    
    name = models.CharField(max_length=200, help_text='Holiday name')
    date = models.DateField(unique=True, help_text='Holiday date')
    holiday_type = models.CharField(
        max_length=20, 
        choices=HOLIDAY_TYPE_CHOICES, 
        default='special',
        help_text='Type of holiday'
    )
    description = models.TextField(blank=True, null=True, help_text='Holiday description')
    is_active = models.BooleanField(default=True)
    is_paid = models.BooleanField(default=True, help_text='Whether employees get paid for this holiday')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_holidays',
        help_text='HR/Manager who created this holiday'
    )
    
    class Meta:
        db_table = 'hr_holiday'
        verbose_name = 'Holiday'
        verbose_name_plural = 'Holidays'
        ordering = ['date']
    
    def __str__(self):
        return f"{self.name} - {self.date} ({self.get_holiday_type_display()})"


class EmployeeLeaveBalance(models.Model):
    """Track leave balances for each employee"""
    user = models.OneToOneField(
        AppUser,
        on_delete=models.CASCADE,
        related_name='leave_balance'
    )
    
    casual_leave_balance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Casual leave balance (accumulates monthly)'
    )
    casual_leave_used = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Casual leave used this year'
    )
    
    sick_leave_balance = models.IntegerField(
        default=3,
        help_text='Sick leave balance for the year'
    )
    sick_leave_used = models.IntegerField(
        default=0,
        help_text='Sick leave used this year'
    )
    
    special_leave_balance = models.IntegerField(
        default=7,
        help_text='Special leave balance for the year'
    )
    special_leave_used = models.IntegerField(
        default=0,
        help_text='Special leave used this year'
    )
    
    unpaid_leave_taken = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Total unpaid leave taken this year'
    )
    
    year = models.IntegerField(default=timezone.now().year)
    last_casual_credit_month = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_employee_leave_balance'
        verbose_name = 'Employee Leave Balance'
        verbose_name_plural = 'Employee Leave Balances'
        unique_together = ['user', 'year']
    
    def __str__(self):
        return f"{self.user.name} - Leave Balance {self.year}"


class LeaveRequest(models.Model):
    """Leave requests using master.LeaveMaster"""
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
    
    leave_master = models.ForeignKey(
        'master.LeaveMaster',
        on_delete=models.PROTECT,
        related_name='hr_leave_requests',
        db_column='leave_master_id',
        to_field='id',
    )

    leave_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text='Deprecated - use leave_master instead'
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
    
    is_paid = models.BooleanField(
        default=True,
        help_text='Auto-set from Leave Master payment status'
    )
    deducted_from_balance = models.BooleanField(
        default=False,
        help_text='Whether leave has been deducted from balance'
    )
    
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
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_leave_request'
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.name} - {self.leave_master.leave_name} - {self.from_date} to {self.to_date}"
    
    @property
    def total_days(self):
        """Calculate total days of leave"""
        delta = self.to_date - self.from_date
        return delta.days + 1
    
    def save(self, *args, **kwargs):
        """Auto-set is_paid and leave_type from leave_master"""
        if self.leave_master:
            self.is_paid = (self.leave_master.payment_status == 'paid')
            if not self.leave_type:
                self.leave_type = self.leave_master.leave_name
        super().save(*args, **kwargs)


class LateRequest(models.Model):
    """Late arrival requests - NO LEAVE MASTER REQUIRED"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='late_requests')
    date = models.DateField()
    late_by_minutes = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(240)])
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    reviewed_by = models.ForeignKey(
        AppUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_late_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_comment = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_late_request'
        verbose_name = 'Late Request'
        verbose_name_plural = 'Late Requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.name} - Late by {self.late_by_minutes} mins on {self.date}"


class EarlyRequest(models.Model):
    """Early departure requests - NO LEAVE MASTER REQUIRED"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='early_requests')
    date = models.DateField()
    early_by_minutes = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(240)])
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    reviewed_by = models.ForeignKey(
        AppUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_early_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_comment = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_early_request'
        verbose_name = 'Early Request'
        verbose_name_plural = 'Early Requests'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.name} - Early by {self.early_by_minutes} mins on {self.date}"


class Attendance(models.Model):
    """Attendance with Leave Master integration"""
    STATUS_CHOICES = [
        ('full', 'Full Day'),
        ('half', 'Half Day'),
        ('leave', 'Leave'),
        ('wfh', 'Work From Home'),
        ('sunday', 'Sunday (Paid)'),
        ('holiday', 'Holiday (Paid)'),
        ('special_leave', 'Special Leave'),
        ('mandatory_holiday', 'Mandatory Holiday'),
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
    
    # Punch times
    first_punch_in_time = models.DateTimeField(null=True, blank=True)
    first_punch_in_location = models.CharField(max_length=255, blank=True, null=True)
    first_punch_in_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    first_punch_in_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    last_punch_out_time = models.DateTimeField(null=True, blank=True)
    last_punch_out_location = models.CharField(max_length=255, blank=True, null=True)
    last_punch_out_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    last_punch_out_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Calculated times
    total_working_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(24)]
    )
    total_break_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(24)]
    )
    
    is_currently_on_break = models.BooleanField(default=False)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='half')
    verification_status = models.CharField(max_length=15, choices=VERIFICATION_CHOICES, default='unverified')
    
    # Holiday tracking
    is_sunday = models.BooleanField(default=False)
    is_holiday = models.BooleanField(default=False)
    holiday = models.ForeignKey(
        Holiday,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendances'
    )
    
    # Leave tracking
    is_leave = models.BooleanField(default=False)
    leave_request = models.ForeignKey(
        LeaveRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendances'
    )
    leave_master = models.ForeignKey(
        'master.LeaveMaster',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendances'
    )
    is_paid_day = models.BooleanField(
        default=True,
        help_text='For payroll: whether this day is paid'
    )
    
    # Notes
    note = models.TextField(blank=True, null=True)
    admin_note = models.TextField(blank=True, null=True)
    
    # Verification
    verified_by = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_attendances'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
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
            models.Index(fields=['is_sunday']),
            models.Index(fields=['is_holiday']),
            models.Index(fields=['is_leave']),
            models.Index(fields=['is_paid_day']),
        ]
    
    def __str__(self):
        return f"{self.user.name} - {self.date} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Override save to automatically mark Sundays and holidays"""
        # Check if this date is a Sunday
        if self.date and self.date.weekday() == 6:
            self.is_sunday = True
            if not self.first_punch_in_time:
                self.status = 'sunday'
                self.is_paid_day = True
                self.verification_status = 'verified'
        
        # Check if this date is a holiday
        if self.date:
            try:
                holiday = Holiday.objects.get(date=self.date, is_active=True)
                self.is_holiday = True
                self.holiday = holiday
                if not self.first_punch_in_time:
                    self.status = 'holiday'
                    self.is_paid_day = holiday.is_paid
                    self.verification_status = 'verified'
            except Holiday.DoesNotExist:
                pass
        
        # Set is_paid_day from leave_master if on leave
        if self.leave_master:
            self.is_paid_day = (self.leave_master.payment_status == 'paid')
        
        super().save(*args, **kwargs)
    
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
                duration = (punch.punch_time - last_in).total_seconds()
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
            last_punch_any = punches.last()
            if last_punch_any and last_punch_any.punch_type == 'in':
                self.is_currently_on_break = True
    
    def update_status(self):
        """Update attendance status based on working hours"""
        if self.status in ['leave', 'holiday', 'sunday']:
            return
        
        if self.total_working_hours >= 7.5:
            self.status = 'full'
        elif self.total_working_hours >= 4:
            self.status = 'half'
        else:
            self.status = 'half'


class PunchRecord(models.Model):
    """Individual punch in/out records"""
    PUNCH_TYPE_CHOICES = [
        ('in', 'Punch In'),
        ('out', 'Punch Out'),
    ]
    
    attendance = models.ForeignKey(
        Attendance,
        on_delete=models.CASCADE,
        related_name='punch_records'
    )
    punch_type = models.CharField(max_length=3, choices=PUNCH_TYPE_CHOICES)
    punch_time = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'hr_punch_record'
        verbose_name = 'Punch Record'
        verbose_name_plural = 'Punch Records'
        ordering = ['punch_time']
    
    def __str__(self):
        return f"{self.attendance.user.name} - {self.get_punch_type_display()} - {self.punch_time}"