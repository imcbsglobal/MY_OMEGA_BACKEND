from django.db import models

# Create your models here.
# delivery_management/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class Delivery(models.Model):
    """
    Main Delivery Model - Tracks complete delivery lifecycle
    """
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Reference to existing models
    employee = models.ForeignKey(
        'employee_management.Employee',
        on_delete=models.PROTECT,
        related_name='deliveries',
        help_text='Delivery person'
    )
    vehicle = models.ForeignKey(
        'vehicle_management.Vehicle',
        on_delete=models.PROTECT,
        related_name='deliveries',
        help_text='Vehicle used for delivery'
    )
    route = models.ForeignKey(
        'target_management.Route',
        on_delete=models.PROTECT,
        related_name='deliveries',
        help_text='Delivery route'
    )

    # Delivery Identification
    delivery_number = models.CharField(
        max_length=50,
        unique=True,
        help_text='Unique delivery number (auto-generated)'
    )

    # Scheduling Information
    scheduled_date = models.DateField(
        help_text='Scheduled delivery date'
    )
    scheduled_time = models.TimeField(
        help_text='Scheduled delivery time'
    )

    # Actual Delivery Timestamps
    start_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Actual delivery start time'
    )
    end_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Actual delivery end time'
    )

    # Odometer Readings
    odometer_start = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Odometer reading at start (km)'
    )
    odometer_end = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Odometer reading at end (km)'
    )

    # Fuel Information
    fuel_start = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Fuel level at start (liters)'
    )
    fuel_end = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Fuel level at end (liters)'
    )

    # Box/Product Summary
    total_loaded_boxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Total boxes loaded at start'
    )
    total_delivered_boxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Total boxes delivered'
    )
    total_balance_boxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Balance boxes returned'
    )

    # Financial Summary
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Total delivery value'
    )
    collected_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Amount collected from customers'
    )
    total_pending_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Total pending/balance amount'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )

    # Notes
    start_notes = models.TextField(
        blank=True,
        help_text='Notes when starting delivery'
    )
    end_notes = models.TextField(
        blank=True,
        help_text='Notes when completing delivery'
    )
    remarks = models.TextField(
        blank=True,
        help_text='General remarks'
    )

    # Location Information
    start_location = models.CharField(
        max_length=500,
        blank=True,
        help_text='Human-readable start location description'
    )
    start_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text='GPS Latitude for delivery start location'
    )
    start_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text='GPS Longitude for delivery start location'
    )
    completion_location = models.CharField(
        max_length=500,
        blank=True,
        help_text='Human-readable completion location description'
    )
    completion_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text='GPS Latitude for delivery completion location'
    )
    completion_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text='GPS Longitude for delivery completion location'
    )

    # Audit Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_deliveries',
        help_text='User who created this delivery'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When this delivery was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When this delivery was last updated'
    )

    # Completion tracking
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_deliveries',
        help_text='User who completed this delivery'
    )

    class Meta:
        db_table = 'delivery_management_delivery'
        verbose_name = 'Delivery'
        verbose_name_plural = 'Deliveries'
        ordering = ['-scheduled_date', '-scheduled_time']
        indexes = [
            models.Index(fields=['delivery_number']),
            models.Index(fields=['employee', 'scheduled_date']),
            models.Index(fields=['vehicle', 'scheduled_date']),
            models.Index(fields=['route', 'scheduled_date']),
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.delivery_number} - {self.employee.get_full_name()} - {self.scheduled_date}"

    def save(self, *args, **kwargs):
        """Auto-generate delivery number if not provided"""
        if not self.delivery_number:
            # Generate delivery number: DEL-YYYYMMDD-XXXX
            from django.db.models import Max
            today = timezone.now().date()
            date_str = today.strftime('%Y%m%d')
            
            # Get last delivery number for today
            last_delivery = Delivery.objects.filter(
                delivery_number__startswith=f'DEL-{date_str}-'
            ).aggregate(Max('delivery_number'))
            
            if last_delivery['delivery_number__max']:
                last_seq = int(last_delivery['delivery_number__max'].split('-')[-1])
                new_seq = last_seq + 1
            else:
                new_seq = 1
            
            self.delivery_number = f'DEL-{date_str}-{new_seq:04d}'
        
        # Auto-calculate balance boxes
        # Use `is not None` so that zero values (0 delivered) still trigger recalculation
        if self.total_loaded_boxes is not None and self.total_delivered_boxes is not None:
            self.total_balance_boxes = max(Decimal('0.00'), self.total_loaded_boxes - self.total_delivered_boxes)
        
        # Auto-calculate pending amount
        if self.total_amount is not None and self.collected_amount is not None:
            self.total_pending_amount = max(Decimal('0.00'), self.total_amount - self.collected_amount)
        
        super().save(*args, **kwargs)

    @property
    def duration_minutes(self):
        """Calculate delivery duration in minutes"""
        if self.start_datetime and self.end_datetime:
            delta = self.end_datetime - self.start_datetime
            return int(delta.total_seconds() / 60)
        return None

    @property
    def distance_traveled(self):
        """Calculate distance traveled"""
        if self.odometer_start and self.odometer_end:
            return self.odometer_end - self.odometer_start
        return None

    @property
    def fuel_consumed(self):
        """Calculate fuel consumed"""
        if self.fuel_start and self.fuel_end:
            return self.fuel_start - self.fuel_end
        return None

    @property
    def delivery_efficiency(self):
        """Calculate delivery efficiency percentage"""
        if self.total_loaded_boxes > 0:
            return (self.total_delivered_boxes / self.total_loaded_boxes) * 100
        return 0

    def can_start(self):
        """Check if delivery can be started"""
        return self.status == 'scheduled'

    def can_complete(self):
        """Check if delivery can be completed"""
        return self.status == 'in_progress'

    def start_delivery(self, user, odometer_reading=None, fuel_level=None, notes='', 
                      start_location='', start_latitude=None, start_longitude=None):
        """Start the delivery"""
        if not self.can_start():
            raise ValueError('Delivery cannot be started in current status')
        
        self.status = 'in_progress'
        self.start_datetime = timezone.now()
        self.odometer_start = odometer_reading
        self.fuel_start = fuel_level
        self.start_notes = notes
        self.start_location = start_location
        self.start_latitude = start_latitude
        self.start_longitude = start_longitude
        self.save()

    def complete_delivery(self, user, odometer_reading=None, fuel_level=None, 
                         delivered_boxes=0, balance_boxes=0, collected_amount=0, notes='',
                         completion_location='', completion_latitude=None, completion_longitude=None):
        """Complete the delivery"""
        if not self.can_complete():
            raise ValueError('Delivery cannot be completed in current status')
        
        self.status = 'completed'
        self.end_datetime = timezone.now()
        self.odometer_end = odometer_reading
        self.fuel_end = fuel_level
        self.total_delivered_boxes = delivered_boxes
        self.total_balance_boxes = balance_boxes
        self.collected_amount = collected_amount
        self.end_notes = notes
        self.completion_location = completion_location
        self.completion_latitude = completion_latitude
        self.completion_longitude = completion_longitude
        self.completed_by = user
        self.save()


class DeliveryProduct(models.Model):
    """
    Products loaded for delivery - tracks loaded, delivered, and balance quantities
    """
    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='products'
    )
    product = models.ForeignKey(
        'target_management.Product',
        on_delete=models.PROTECT,
        related_name='delivery_items'
    )

    # Quantities
    loaded_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Quantity loaded at start'
    )
    delivered_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Quantity actually delivered'
    )
    balance_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Balance quantity returned'
    )

    # Pricing
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Price per unit'
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Total amount for this product'
    )

    # Additional Info
    notes = models.TextField(
        blank=True,
        help_text='Product-specific notes'
    )

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'delivery_management_delivery_product'
        verbose_name = 'Delivery Product'
        verbose_name_plural = 'Delivery Products'
        ordering = ['product__product_name']
        unique_together = ['delivery', 'product']

    def __str__(self):
        return f"{self.delivery.delivery_number} - {self.product.product_name}"

    def save(self, *args, **kwargs):
        """Auto-calculate balance and total amount"""
        # Calculate balance
        if self.loaded_quantity and self.delivered_quantity is not None:
            self.balance_quantity = self.loaded_quantity - self.delivered_quantity
        
        # Calculate total amount
        if self.delivered_quantity and self.unit_price:
            self.total_amount = self.delivered_quantity * self.unit_price
        
        super().save(*args, **kwargs)

    @property
    def delivery_percentage(self):
        """Calculate delivery percentage"""
        if self.loaded_quantity > 0:
            return (self.delivered_quantity / self.loaded_quantity) * 100
        return 0


class DeliveryStop(models.Model):
    """
    Individual delivery stops/locations during the delivery
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ]

    delivery = models.ForeignKey(
        Delivery,
        on_delete=models.CASCADE,
        related_name='stops'
    )

    # Stop Information
    stop_sequence = models.PositiveIntegerField(
        help_text='Order of this stop in the delivery route'
    )
    customer_name = models.CharField(
        max_length=255,
        help_text='Customer/Location name'
    )
    customer_address = models.TextField(
        help_text='Delivery address'
    )
    customer_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Customer contact number'
    )

    # Delivery Details
    planned_boxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Planned boxes for this stop'
    )
    delivered_boxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Actually delivered boxes at this stop'
    )
    balance_boxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Balance boxes remaining after this stop'
    )
    planned_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Planned delivery amount'
    )
    collected_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Cash collected at this stop'
    )
    pending_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Pending/Balance amount at this stop'
    )

    # Timing
    estimated_arrival = models.TimeField(
        null=True,
        blank=True,
        help_text='Estimated arrival time'
    )
    actual_arrival = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Actual arrival time'
    )
    departure_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Departure time from this stop'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Notes for this stop'
    )
    failure_reason = models.TextField(
        blank=True,
        help_text='Reason if delivery failed/skipped'
    )

    # Signature/Proof
    signature_image = models.ImageField(
        upload_to='deliveries/signatures/',
        null=True,
        blank=True,
        help_text='Customer signature'
    )
    proof_image = models.ImageField(
        upload_to='deliveries/proofs/',
        null=True,
        blank=True,
        help_text='Delivery proof photo'
    )

    # Location
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text='GPS Latitude'
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text='GPS Longitude'
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'delivery_management_delivery_stop'
        verbose_name = 'Delivery Stop'
        verbose_name_plural = 'Delivery Stops'
        ordering = ['delivery', 'stop_sequence']
        unique_together = ['delivery', 'stop_sequence']

    def __str__(self):
        return f"{self.delivery.delivery_number} - Stop {self.stop_sequence} - {self.customer_name}"

    def save(self, *args, **kwargs):
        """Auto-calculate balance boxes and pending amount"""
        # Calculate balance boxes if delivered quantity is provided
        if self.delivered_boxes is not None and self.planned_boxes:
            self.balance_boxes = max(Decimal('0.00'), self.planned_boxes - self.delivered_boxes)
        
        # Calculate pending amount if collected amount is provided
        if self.collected_amount is not None and self.planned_amount:
            self.pending_amount = max(Decimal('0.00'), self.planned_amount - self.collected_amount)
        
        super().save(*args, **kwargs)

    @property
    def stop_duration(self):
        """Calculate time spent at this stop"""
        if self.actual_arrival and self.departure_time:
            delta = self.departure_time - self.actual_arrival
            return int(delta.total_seconds() / 60)
        return None

    @property
    def is_completed(self):
        """Check if stop is completed"""
        return self.status in ['delivered', 'partial', 'failed', 'skipped']