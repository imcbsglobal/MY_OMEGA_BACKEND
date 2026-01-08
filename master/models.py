from django.db import models

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.leave_name
