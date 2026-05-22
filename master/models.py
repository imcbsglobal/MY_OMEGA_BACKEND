# master/models.py
from django.db import models
from django.utils import timezone

class LeaveMaster(models.Model):
    LEAVE_CATEGORIES = [
        ('casual', 'Casual Leave'),
        ('sick', 'Sick Leave'),
        ('special', 'Special Leave'),
        ('mandatory_holiday', 'Mandatory Holiday'),
    ]

    PAYMENT_STATUS = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
    ]

    leave_name = models.CharField(max_length=100)
    leave_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=30, choices=LEAVE_CATEGORIES)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True, help_text='Description of the leave type')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Leave Master'
        verbose_name_plural = 'Leave Masters'
        ordering = ['leave_date', 'leave_name']

    def __str__(self):
        return self.leave_name


class AssetMaster(models.Model):
    asset_name = models.CharField(max_length=255, verbose_name='Asset Name')
    asset_id = models.CharField(max_length=128, unique=True, verbose_name='Asset ID')
    asset_category = models.CharField(max_length=128, verbose_name='Asset Category')
    serial_number = models.CharField(max_length=128, blank=True, null=True, verbose_name='Serial Number')
    
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'master_asset_master'
        ordering = ['-created_at', 'asset_name']
        verbose_name = 'Asset Master'
        verbose_name_plural = 'Asset Masters'

    def __str__(self):
        return f'{self.asset_name} ({self.asset_id})'