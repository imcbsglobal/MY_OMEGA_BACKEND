# HR/models.py - Updated with unified LeaveMaster model
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from User.models import AppUser
from decimal import Decimal


class Holiday(models.Model):
    """
    Model to store company holidays
    Includes mandatory holidays (paid) and special holidays
    """
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
    """
    Track leave balances for each employee
    """
    user = models.OneToOneField(
        AppUser,
        on_delete=models.CASCADE,
        related_name='leave_balance'
    )
    
    # Casual Leave - 1 per month, carries forward
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
    
    # Sick Leave - 3 per year
    sick_leave_balance = models.IntegerField(
        default=3,
        help_text='Sick leave balance for the year'
    )
    sick_leave_used = models.IntegerField(
        default=0,
        help_text='Sick leave used this year'
    )
    
    # Special Leave - 7 per year (HR can mark)
    special_leave_balance = models.IntegerField(
        default=7,
        help_text='Special leave balance for the year'
    )
    special_leave_used = models.IntegerField(
        default=0,
        help_text='Special leave used this year'
    )
    
    # Unpaid Leave tracking
    unpaid_leave_taken = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Total unpaid leave taken this year'
    )
    
    # Year tracking
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
    
    def credit_monthly_casual_leave(self, month):
        """Credit 1 casual leave for the month if not already credited"""
        if self.last_casual_credit_month < month:
            self.casual_leave_balance += Decimal('1.0')
            self.last_casual_credit_month = month
            self.save()
            return True
        return False
    
    def reset_yearly_balances(self):
        """Reset balances at the start of new year"""
        self.sick_leave_balance = 3
        self.sick_leave_used = 0
        self.special_leave_balance = 7
        self.special_leave_used = 0
        self.casual_leave_used = 0
        self.unpaid_leave_taken = 0
        self.last_casual_credit_month = 0
        # Casual leave carries forward, don't reset
        self.save()
    
    def has_sufficient_balance(self, leave_type, days):
        """Check if employee has sufficient leave balance"""
        if leave_type == 'casual':
            return self.casual_leave_balance >= Decimal(str(days))
        elif leave_type == 'sick':
            return self.sick_leave_balance >= days
        elif leave_type == 'special':
            return self.special_leave_balance >= days
        return True  # Unpaid leave always available


# HR/models.py - LeaveMaster Model Section
from django.db import models
from django.utils import timezone
from User.models import AppUser

class LeaveMaster(models.Model):
    """
    Master table for managing different types of leaves
    """
    CATEGORY_CHOICES = [
        ('festival', 'Festival Leave'),
        ('national', 'National Holiday'),
        ('company', 'Company Holiday'),
        ('special', 'Special Leave'),
        ('casual', 'Casual Leave'),
        ('sick', 'Sick Leave'),
        ('earned', 'Earned Leave'),
        ('emergency', 'Emergency Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('mandatory_holiday', 'Mandatory Holiday'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('paid', 'Paid Leave'),
        ('unpaid', 'Unpaid Leave'),
    ]
    
    leave_name = models.CharField(max_length=200, help_text='Name of the leave (e.g., Diwali, Christmas)')
    leave_date = models.DateField(null=True, blank=True, help_text='Specific date for the leave (optional)')
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='special',
        help_text='Category of leave'
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='paid',
        help_text='Whether this leave is paid or unpaid'
    )
    description = models.TextField(blank=True, null=True, help_text='Description of the leave')
    is_active = models.BooleanField(default=True, help_text='Whether this leave type is currently active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_leave_masters',
        help_text='Admin who created this leave type'
    )
    
    class Meta:
        db_table = 'hr_leave_master'
        verbose_name = 'Leave Master'
        verbose_name_plural = 'Leave Masters'
        ordering = ['leave_date', 'leave_name']
    
    def __str__(self):
        return f"{self.leave_name} ({self.get_category_display()})"


class LeaveRequest(models.Model):
    """
    Model to store leave requests from employees
    UPDATED: Added link to LeaveMaster
    """
    LEAVE_TYPE_CHOICES = [
        ('casual', 'Casual Leave (Paid)'),
        ('sick', 'Sick Leave (Paid)'),
        ('special', 'Special Leave (Paid)'),
        ('unpaid', 'Unpaid Leave'),
        ('emergency', 'Emergency Leave'),
        ('earned', 'Earned Leave'),
        ('leave_master', 'Leave Master Type'),  # For LeaveMaster based leaves
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
    
    # Link to Leave Master (optional)
    leave_master = models.ForeignKey(
        LeaveMaster,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leave_requests',
        help_text='Leave Master entry if this request is based on a predefined leave'
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
    
    # Leave balance tracking
    is_paid = models.BooleanField(
        default=True,
        help_text='Whether this leave is paid or unpaid'
    )
    deducted_from_balance = models.BooleanField(
        default=False,
        help_text='Whether leave has been deducted from balance'
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
        if self.leave_master:
            return f"{self.user.name} - {self.leave_master.leave_name} - {self.from_date} to {self.to_date}"
        return f"{self.user.name} - {self.leave_type} - {self.from_date} to {self.to_date}"
    
    @property
    def total_days(self):
        """Calculate total days of leave"""
        delta = self.to_date - self.from_date
        return delta.days + 1
    
    def get_leave_display_name(self):
        """Get the display name for the leave"""
        if self.leave_master:
            return self.leave_master.leave_name
        return self.get_leave_type_display()
    
    def save(self, *args, **kwargs):
        """Override save to auto-set is_paid based on leave_master"""
        if self.leave_master:
            self.is_paid = (self.leave_master.payment_status == 'paid')
            # Set leave_type to 'leave_master' if using LeaveMaster
            if not self.leave_type or self.leave_type == 'leave_master':
                self.leave_type = 'leave_master'
        super().save(*args, **kwargs)
    
    def approve_and_deduct_balance(self, approved_by):
        """Approve leave and deduct from employee's balance"""
        if self.status == 'approved' and self.deducted_from_balance:
            return False, "Leave already approved and deducted"
        
        # Get or create leave balance for current year
        balance, created = EmployeeLeaveBalance.objects.get_or_create(
            user=self.user,
            year=self.from_date.year,
            defaults={
                'casual_leave_balance': 0,
                'sick_leave_balance': 3,
                'special_leave_balance': 7,
            }
        )
        
        days = self.total_days
        
        # Check and deduct based on leave type
        if self.leave_type == 'casual':
            if balance.casual_leave_balance >= Decimal(str(days)):
                balance.casual_leave_balance -= Decimal(str(days))
                balance.casual_leave_used += Decimal(str(days))
                self.is_paid = True
            else:
                # Convert to unpaid if insufficient balance
                balance.unpaid_leave_taken += Decimal(str(days))
                self.is_paid = False
                self.leave_type = 'unpaid'
                
        elif self.leave_type == 'sick':
            if balance.sick_leave_balance >= days:
                balance.sick_leave_balance -= days
                balance.sick_leave_used += days
                self.is_paid = True
            else:
                # Convert to unpaid if insufficient balance
                balance.unpaid_leave_taken += Decimal(str(days))
                self.is_paid = False
                self.leave_type = 'unpaid'
                
        elif self.leave_type == 'special':
            if balance.special_leave_balance >= days:
                balance.special_leave_balance -= days
                balance.special_leave_used += days
                self.is_paid = True
            else:
                return False, "Insufficient special leave balance. HR must approve."
                
        elif self.leave_type == 'unpaid':
            balance.unpaid_leave_taken += Decimal(str(days))
            self.is_paid = False
        
        balance.save()
        
        self.status = 'approved'
        self.reviewed_by = approved_by
        self.reviewed_at = timezone.now()
        self.deducted_from_balance = True
        self.save()
        
        return True, "Leave approved successfully"


class Attendance(models.Model):
    """
    Model to store daily attendance records with multiple punch in/out
    Enhanced with leave tracking
    """
    STATUS_CHOICES = [
        ('full', 'Full Day'),
        ('half', 'Half Day'),
        ('leave', 'Leave'),
        ('casual_leave', 'Casual Leave (Paid)'),
        ('sick_leave', 'Sick Leave (Paid)'),
        ('special_leave', 'Special Leave (Paid)'),
        ('unpaid_leave', 'Unpaid Leave'),
        ('mandatory_holiday', 'Mandatory Holiday (Paid)'),
        ('special_holiday', 'Special Holiday (Paid)'),
        ('sunday', 'Sunday (Paid)'),
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
    first_punch_in_time = models.DateTimeField(null=True, blank=True)
    first_punch_in_location = models.CharField(max_length=255, blank=True, null=True)
    first_punch_in_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    first_punch_in_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Last Punch Out (End of Day)
    last_punch_out_time = models.DateTimeField(null=True, blank=True)
    last_punch_out_location = models.CharField(max_length=255, blank=True, null=True)
    last_punch_out_latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    last_punch_out_longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    
    # Calculated Times
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
    
    # Status and Verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='half')
    verification_status = models.CharField(max_length=15, choices=VERIFICATION_CHOICES, default='unverified')
    
    # Holiday tracking
    is_sunday = models.BooleanField(default=False, help_text='Automatically marked as Sunday')
    is_holiday = models.BooleanField(default=False, help_text='Holiday day')
    holiday = models.ForeignKey(
        Holiday,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendances',
        help_text='Associated holiday if applicable'
    )
    
    # Leave tracking
    is_paid_leave = models.BooleanField(
        default=False,
        help_text='Whether this is a paid leave day'
    )
    leave_type = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Type of leave if applicable'
    )
    
    # Notes
    note = models.TextField(blank=True, null=True)
    admin_note = models.TextField(blank=True, null=True)
    
    # Admin actions
    verified_by = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_attendances'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
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
            models.Index(fields=['is_sunday']),
            models.Index(fields=['is_holiday']),
        ]
    
    def __str__(self):
        return f"{self.user.name} - {self.date} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Override save to automatically mark Sundays and holidays"""
        # Check if this date is a Sunday
        if self.date and self.date.weekday() == 6:  # 6 = Sunday
            self.is_sunday = True
            if not self.first_punch_in_time:  # Only set if not manually marked
                self.status = 'sunday'
                self.verification_status = 'verified'
        
        # Check if this date is a holiday
        if self.date:
            try:
                holiday = Holiday.objects.get(date=self.date, is_active=True)
                self.is_holiday = True
                self.holiday = holiday
                if not self.first_punch_in_time:  # Only set if not manually marked
                    if holiday.holiday_type == 'mandatory':
                        self.status = 'mandatory_holiday'
                    elif holiday.holiday_type == 'special':
                        self.status = 'special_holiday'
                    self.verification_status = 'verified'
            except Holiday.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
    
    def is_paid_day(self):
        """Check if this day counts as paid"""
        paid_statuses = [
            'full', 'half', 'casual_leave', 'sick_leave', 
            'special_leave', 'mandatory_holiday', 'special_holiday', 
            'sunday', 'wfh'
        ]
        return self.status in paid_statuses
    
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
        """Update attendance status based on working hours and leave type"""
        # Don't change status if it's a special day
        if self.status in ['casual_leave', 'sick_leave', 'special_leave', 
                          'unpaid_leave', 'mandatory_holiday', 'special_holiday', 'sunday']:
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


class LateRequest(models.Model):
    """Late arrival requests"""
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
    reviewed_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_late_requests')
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
    """Early departure requests"""
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
    reviewed_by = models.ForeignKey(AppUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_early_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_comment = models.TextField(blank=True, null=True)
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