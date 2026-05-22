from django.conf import settings
from django.db import models
from django.utils import timezone


class Asset(models.Model):
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('damaged', 'Damaged'),
        ('needs_repair', 'Needs Repair'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('returned', 'Returned'),
        ('maintenance', 'Maintenance'),
        ('retired', 'Retired'),
    ]

    asset_name = models.CharField(max_length=255, verbose_name='Asset Name')
    asset_tag = models.CharField(max_length=128, unique=True, verbose_name='Asset Tag / ID')
    category = models.CharField(max_length=128, verbose_name='Category')
    serial_number = models.CharField(max_length=128, blank=True, null=True, verbose_name='Serial Number')

    employee = models.ForeignKey(
        'employee_management.Employee',
        on_delete=models.PROTECT,
        related_name='assets',
        verbose_name='Employee Name',
    )

    description = models.TextField(blank=True, null=True, verbose_name='Description')
    condition = models.CharField(max_length=32, choices=CONDITION_CHOICES, default='good')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='available')
    assigned_date = models.DateField(null=True, blank=True, verbose_name='Assigned Date')
    return_date = models.DateField(null=True, blank=True, verbose_name='Return Date')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_assets',
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'asset_management_asset'
        ordering = ['-assigned_date', '-created_at', '-id']
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'

    def __str__(self):
        return f'{self.asset_name} ({self.asset_tag})'
