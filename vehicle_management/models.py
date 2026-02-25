from django.db import models

# Create your models here.
# vehicle_management/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Vehicle(models.Model):
    """
    Vehicle Master - stores all vehicle information
    """
    # Basic Information
    vehicle_name = models.CharField(
        max_length=255,
        help_text='Vehicle name or model',
        verbose_name='Vehicle Name'
    )
    company = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        help_text='Vehicle manufacturer/company',
        verbose_name='Company/Brand'
    )
    registration_number = models.CharField(
        max_length=64,
        unique=True,
        help_text='Vehicle registration/license plate number',
        verbose_name='Registration Number'
    )
    
    # Vehicle Details
    vehicle_type = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        choices=[
            ('car', 'Car'),
            ('bike', 'Bike'),
            ('van', 'Van'),
            ('truck', 'Truck'),
            ('bus', 'Bus'),
            ('other', 'Other'),
        ],
        default='car',
        verbose_name='Vehicle Type'
    )
    
    fuel_type = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        choices=[
            ('petrol', 'Petrol'),
            ('diesel', 'Diesel'),
            ('electric', 'Electric'),
            ('hybrid', 'Hybrid'),
            ('cng', 'CNG'),
        ],
        verbose_name='Fuel Type'
    )
    
    color = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name='Color'
    )
    
    manufacturing_year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Manufacturing Year'
    )
    
    seating_capacity = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Seating Capacity'
    )
    
    # Photo
    photo = models.ImageField(
        upload_to='vehicles/photos/',
        null=True,
        blank=True,
        help_text='Vehicle photo',
        verbose_name='Vehicle Photo'
    )
    
    # Ownership & Insurance
    owner_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Owner Name'
    )
    
    insurance_number = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name='Insurance Number'
    )
    
    insurance_expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Insurance Expiry Date'
    )
    
    # Maintenance
    last_service_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Last Service Date'
    )
    
    next_service_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Next Service Date'
    )
    
    current_odometer = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Current odometer reading in KM',
        verbose_name='Current Odometer (KM)'
    )
    
    # Additional Information
    chassis_number = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name='Chassis Number'
    )
    
    engine_number = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        verbose_name='Engine Number'
    )
    
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Notes'
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text='Is vehicle currently active/available',
        verbose_name='Active Status'
    )
    
    # Audit Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_vehicles'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehicle_management_vehicle'
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'
        ordering = ['registration_number']
    
    def __str__(self):
        return f"{self.registration_number} - {self.vehicle_name}"
    
    @property
    def total_trips(self):
        return self.trips.count()
    
    @property
    def total_distance_traveled(self):
        """Calculate total distance traveled from completed trips"""
        from django.db.models import Sum
        result = self.trips.filter(
            status='completed'
        ).aggregate(
            total=Sum('distance_km')
        )
        return result['total'] or Decimal('0.00')
    
    @property
    def total_challans(self):
        """Get total number of challans for this vehicle"""
        return self.challans.count()
    
    @property
    def unpaid_challans_count(self):
        """Get count of unpaid challans"""
        return self.challans.filter(payment_status='unpaid').count()
    
    @property
    def total_fine_amount(self):
        """Calculate total fine amount from all challans"""
        from django.db.models import Sum
        result = self.challans.aggregate(total=Sum('fine_amount'))
        return result['total'] or Decimal('0.00')


class Trip(models.Model):
    """
    Trip/Travel Management - tracks employee trips
    """
    
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    TIME_PERIOD_CHOICES = [
        ('AM', 'AM'),
        ('PM', 'PM'),
    ]
    
    # Trip Basic Information
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name='trips',
        verbose_name='Vehicle'
    )
    
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='trips',
        verbose_name='Employee/Traveled By',
        help_text='Employee who is making the trip'
    )
    
    # Trip Details
    date = models.DateField(
        verbose_name='Trip Date'
    )
    
    start_time = models.TimeField(
        verbose_name='Start Time'
    )
    
    time_period = models.CharField(
        max_length=2,
        choices=TIME_PERIOD_CHOICES,
        default='AM',
        verbose_name='Time Period (AM/PM)'
    )
    
    # Client & Purpose
    client_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Client Name'
    )
    
    purpose = models.TextField(
        null=True,
        blank=True,
        verbose_name='Purpose of Trip'
    )
    
    # Fuel & Odometer - START
    fuel_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=0.00,
        verbose_name='Fuel Cost (₹)'
    )
    
    odometer_start = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Odometer Start (KM)'
    )
    
    odometer_start_image = models.ImageField(
        upload_to='trips/odometer_start/',
        null=True,
        blank=True,
        verbose_name='Odometer Start Image'
    )
    
    # Trip END Information
    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='End Time'
    )
    
    odometer_end = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Odometer End (KM)'
    )
    
    odometer_end_image = models.ImageField(
        upload_to='trips/odometer_end/',
        null=True,
        blank=True,
        verbose_name='Odometer End Image'
    )
    
    # Calculated Fields
    distance_km = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Distance (KM)',
        help_text='Auto-calculated from odometer readings'
    )
    
    duration_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Duration (Hours)',
        help_text='Auto-calculated from start and end time'
    )
    
    # Status
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default='started',
        verbose_name='Trip Status'
    )
    
    # Admin Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_trips',
        verbose_name='Approved By'
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Approved At'
    )
    
    admin_notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Admin Notes/Remarks'
    )
    
    # Audit Fields
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Completed At'
    )
    
    class Meta:
        db_table = 'vehicle_management_trip'
        verbose_name = 'Trip'
        verbose_name_plural = 'Trips'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Trip #{self.id} - {self.vehicle.registration_number} - {self.employee}"
    
    def save(self, *args, **kwargs):
        """Auto-calculate distance and duration before saving"""
        
        # Calculate distance if both odometer readings are present
        if self.odometer_end and self.odometer_start:
            self.distance_km = self.odometer_end - self.odometer_start
        
        # Calculate duration if both times are present
        if self.end_time and self.start_time:
            from datetime import datetime, timedelta
            start_dt = datetime.combine(self.date, self.start_time)
            end_dt = datetime.combine(self.date, self.end_time)
            
            # Handle overnight trips
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            
            duration = end_dt - start_dt
            self.duration_hours = Decimal(duration.total_seconds() / 3600)
        
        # Set completed_at when status changes to completed
        if self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Update vehicle's current odometer reading
        if self.odometer_end and self.status == 'completed':
            self.vehicle.current_odometer = self.odometer_end
            self.vehicle.save(update_fields=['current_odometer'])
    
    @property
    def employee_name(self):
        """Get employee name"""
        if hasattr(self.employee, 'get_full_name'):
            return self.employee.get_full_name()
        return str(self.employee)


class VehicleChallan(models.Model):
    """
    Vehicle Challan/Traffic Fine Management - tracks traffic violations and fines
    """
    
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ]
    
    # Basic Information
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name='challans',
        verbose_name='Vehicle'
    )
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='vehicle_challans',
        verbose_name='Vehicle Owner',
        help_text='Owner responsible for the challan'
    )
    
    # Challan Details
    detail_date = models.DateField(
        verbose_name='Detail Date',
        help_text='Date when the violation occurred'
    )
    
    challan_number = models.CharField(
        max_length=128,
        unique=True,
        verbose_name='Challan Number',
        help_text='Unique challan/ticket number'
    )
    
    challan_date = models.DateField(
        verbose_name='Challan Date',
        help_text='Date when the challan was issued'
    )
    
    # Violation Details
    offence_type = models.CharField(
        max_length=255,
        verbose_name='Offence Type',
        help_text='Type of traffic violation (e.g., Speeding, Parking, Red Light)'
    )
    
    location = models.CharField(
        max_length=255,
        verbose_name='Location',
        help_text='Location where the violation occurred'
    )
    
    # Fine Details
    fine_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Fine Amount (₹)',
        help_text='Amount of fine to be paid'
    )
    
    payment_status = models.CharField(
        max_length=32,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid',
        verbose_name='Payment Status'
    )
    
    payment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Payment Date',
        help_text='Date when the fine was paid'
    )
    
    # Additional Information
    remarks = models.TextField(
        null=True,
        blank=True,
        verbose_name='Remarks/Notes',
        help_text='Any additional notes or comments'
    )
    
    # Attachments
    challan_document = models.FileField(
        upload_to='challans/documents/',
        null=True,
        blank=True,
        verbose_name='Challan Document',
        help_text='Upload challan receipt/document'
    )
    
    payment_receipt = models.FileField(
        upload_to='challans/receipts/',
        null=True,
        blank=True,
        verbose_name='Payment Receipt',
        help_text='Upload payment receipt if paid'
    )
    
    # Audit Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_challans',
        verbose_name='Created By'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vehicle_management_challan'
        verbose_name = 'Vehicle Challan'
        verbose_name_plural = 'Vehicle Challans'
        ordering = ['-challan_date', '-created_at']
    
    def __str__(self):
        return f"Challan {self.challan_number} - {self.vehicle.registration_number}"
    
    def save(self, *args, **kwargs):
        """Auto-set payment date when status changes to paid"""
        if self.payment_status == 'paid' and not self.payment_date:
            self.payment_date = timezone.now().date()
        super().save(*args, **kwargs)
    
    @property
    def is_paid(self):
        """Check if challan is paid"""
        return self.payment_status == 'paid'
    
    @property
    def days_since_challan(self):
        """Calculate days since challan was issued"""
        from datetime import date
        return (date.today() - self.challan_date).days