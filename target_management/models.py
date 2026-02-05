# target_management/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta


class Route(models.Model):
    """
    Route Master - Origin and Destination combinations for target management
    """
    origin = models.CharField(
        max_length=100,
        help_text='Origin location'
    )
    destination = models.CharField(
        max_length=100,
        help_text='Destination location'
    )
    route_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text='Unique route code/identifier (optional)'
    )
    description = models.TextField(
        blank=True,
        help_text='Route description or notes'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Is this route currently active?'
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_routes',
        help_text='User who created this route'
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='When this route was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When this route was last updated'
    )

    class Meta:
        db_table = 'target_management_route'
        verbose_name = 'Route'
        verbose_name_plural = 'Routes'
        ordering = ['origin', 'destination']
        # Enforce unique origin-destination combinations
        unique_together = [['origin', 'destination']]
        indexes = [
            models.Index(fields=['origin', 'destination']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        """String representation of the route"""
        code = f" ({self.route_code})" if self.route_code else ""
        return f"{self.origin} → {self.destination}{code}"
    
    @property
    def route_name(self):
        """Display name for the route"""
        return f"{self.origin} → {self.destination}"
    
    def clean(self):
        """Validate model constraints"""
        from django.core.exceptions import ValidationError
        
        # Ensure origin and destination are different
        if self.origin and self.destination:
            if self.origin.strip().lower() == self.destination.strip().lower():
                raise ValidationError({
                    'destination': 'Origin and destination must be different.'
                })
    
    def save(self, *args, **kwargs):
        """Override save to run clean validation"""
        self.full_clean()
        super().save(*args, **kwargs)


# ... (rest of your Product, RouteTargetPeriod, etc. models remain the same)


class Product(models.Model):
    """
    Product Master - Products for route targets
    """
    product_name = models.CharField(
        max_length=255,
        help_text='Product name'
    )
    product_code = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text='Unique product code/SKU'
    )
    description = models.TextField(null=True, blank=True)
    unit = models.CharField(
        max_length=50,
        default='Pcs',
        help_text='Unit of measurement (e.g., Pcs, Kg, Box, Ltr)'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'target_management_product'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['product_name']

    def __str__(self):
        return f"{self.product_name} ({self.product_code or 'N/A'})"


class RouteTargetPeriod(models.Model):
    """
    Route Target Period - Main target assignment for employee with date range
    """
    employee = models.ForeignKey(
        'employee_management.Employee',
        on_delete=models.CASCADE,
        related_name='route_targets'
    )
    start_date = models.DateField(
        help_text='Start date of the target period'
    )
    end_date = models.DateField(
        help_text='End date of the target period'
    )
    route = models.ForeignKey(
        Route,
        on_delete=models.CASCADE,
        related_name='target_periods'
    )
    target_boxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Target in boxes/units'
    )
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Target amount in currency'
    )
    
    # Achievement tracking
    achieved_boxes = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Boxes achieved'
    )
    achieved_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Amount achieved'
    )
    
    notes = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_route_targets'
    )
    assigned_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'target_management_route_target_period'
        verbose_name = 'Route Target Period'
        verbose_name_plural = 'Route Target Periods'
        ordering = ['-start_date', '-end_date']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError('End date must be after start date')

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.route} - {self.start_date} to {self.end_date}"
    
    @property
    def duration_days(self):
        """Calculate duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    @property
    def period_display(self):
        """Display formatted period"""
        return f"{self.start_date.strftime('%d %b %Y')} - {self.end_date.strftime('%d %b %Y')}"
    
    @property
    def achievement_percentage_boxes(self):
        if self.target_boxes > 0:
            return (self.achieved_boxes / self.target_boxes) * 100
        return 0
    
    @property
    def achievement_percentage_amount(self):
        if self.target_amount > 0:
            return (self.achieved_amount / self.target_amount) * 100
        return 0


class RouteTargetProductDetail(models.Model):
    """
    Product-wise breakdown for route targets
    """
    route_target_period = models.ForeignKey(
        RouteTargetPeriod,
        on_delete=models.CASCADE,
        related_name='product_details'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='route_target_details'
    )
    target_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    achieved_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'target_management_route_target_product_detail'
        verbose_name = 'Route Target Product Detail'
        verbose_name_plural = 'Route Target Product Details'
        unique_together = ['route_target_period', 'product']

    def __str__(self):
        return f"{self.route_target_period} - {self.product.product_name}"
    
    @property
    def achievement_percentage(self):
        if self.target_quantity > 0:
            return (self.achieved_quantity / self.target_quantity) * 100
        return 0


class CallTargetPeriod(models.Model):
    """
    Call Target Period - Call targets for employees with date range
    """
    employee = models.ForeignKey(
        'employee_management.Employee',
        on_delete=models.CASCADE,
        related_name='call_targets'
    )
    start_date = models.DateField(
        help_text='Start date of the target period'
    )
    end_date = models.DateField(
        help_text='End date of the target period'
    )
    
    notes = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_call_targets'
    )
    assigned_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'target_management_call_target_period'
        verbose_name = 'Call Target Period'
        verbose_name_plural = 'Call Target Periods'
        ordering = ['-start_date', '-end_date']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError('End date must be after start date')

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.start_date} to {self.end_date}"
    
    @property
    def duration_days(self):
        """Calculate duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    @property
    def period_display(self):
        """Display formatted period"""
        return f"{self.start_date.strftime('%d %b %Y')} - {self.end_date.strftime('%d %b %Y')}"
    
    @property
    def total_target_calls(self):
        return sum([dt.target_calls for dt in self.daily_targets.all()])
    
    @property
    def total_achieved_calls(self):
        return sum([dt.achieved_calls for dt in self.daily_targets.all()])
    
    @property
    def achievement_percentage(self):
        total_target = self.total_target_calls
        if total_target > 0:
            return (self.total_achieved_calls / total_target) * 100
        return 0


class CallDailyTarget(models.Model):
    """
    Daily Call Targets - Individual day targets
    """
    call_target_period = models.ForeignKey(
        CallTargetPeriod,
        on_delete=models.CASCADE,
        related_name='daily_targets'
    )
    target_date = models.DateField(
        help_text='Specific date for this target'
    )
    target_calls = models.IntegerField(
        default=0,
        help_text='Number of calls targeted for this day'
    )
    achieved_calls = models.IntegerField(
        default=0,
        help_text='Number of calls achieved'
    )
    
    # Additional daily metrics
    productive_calls = models.IntegerField(
        default=0,
        help_text='Productive/successful calls'
    )
    order_received = models.IntegerField(
        default=0,
        help_text='Orders received'
    )
    order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Total order amount'
    )
    
    remarks = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'target_management_call_daily_target'
        verbose_name = 'Call Daily Target'
        verbose_name_plural = 'Call Daily Targets'
        ordering = ['target_date']
        unique_together = ['call_target_period', 'target_date']

    def __str__(self):
        return f"{self.call_target_period.employee.get_full_name()} - {self.target_date}"
    
    @property
    def day_name(self):
        """Get day name (Monday, Tuesday, etc.)"""
        return self.target_date.strftime('%A')
    
    @property
    def achievement_percentage(self):
        if self.target_calls > 0:
            return (self.achieved_calls / self.target_calls) * 100
        return 0
    
    @property
    def productivity_percentage(self):
        if self.achieved_calls > 0:
            return (self.productive_calls / self.achieved_calls) * 100
        return 0


class TargetAchievementLog(models.Model):
    """
    Log for tracking daily achievements and updates
    """
    LOG_TYPE_CHOICES = [
        ('route', 'Route Target'),
        ('call', 'Call Target'),
    ]

    log_type = models.CharField(max_length=20, choices=LOG_TYPE_CHOICES)
    employee = models.ForeignKey(
        'employee_management.Employee',
        on_delete=models.CASCADE,
        related_name='achievement_logs'
    )
    
    # Reference fields (only one should be filled)
    route_target = models.ForeignKey(
        RouteTargetPeriod,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='achievement_logs'
    )
    call_daily_target = models.ForeignKey(
        CallDailyTarget,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='achievement_logs'
    )
    
    achievement_date = models.DateField(default=timezone.now)
    achievement_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Achievement value (quantity/amount/calls)'
    )
    remarks = models.TextField(null=True, blank=True)
    
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recorded_achievements'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'target_management_achievement_log'
        verbose_name = 'Target Achievement Log'
        verbose_name_plural = 'Target Achievement Logs'
        ordering = ['-achievement_date', '-created_at']

    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.log_type} - {self.achievement_date}"