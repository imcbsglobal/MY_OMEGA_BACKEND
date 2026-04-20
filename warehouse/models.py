from django.db import models
from django.conf import settings
from datetime import timedelta


class WarehouseTask(models.Model):
    STATUS_PENDING = 'Pending'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_COMPLETED = 'Completed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    task_title = models.CharField(max_length=255)
    description = models.TextField()
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='warehouse_tasks_assigned_by',
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='warehouse_tasks_assigned_to',
    )
    assigned_date = models.DateField()
    due_date = models.DateField()
    total_work = models.IntegerField()
    completed_work = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    remarks = models.TextField(null=True, blank=True)
    start_datetime = models.DateTimeField(null=True, blank=True)
    completed_datetime = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Warehouse Task'
        verbose_name_plural = 'Warehouse Tasks'

    def save(self, *args, **kwargs):
        from django.utils import timezone
        
        # Set start_datetime when status changes to "In Progress"
        if self.status == self.STATUS_IN_PROGRESS and not self.start_datetime:
            self.start_datetime = timezone.now()
        
        # Auto-update status based on completed_work
        if self.completed_work >= self.total_work and self.total_work > 0:
            self.status = self.STATUS_COMPLETED
            # Set completed_datetime when status changes to "Completed"
            if not self.completed_datetime:
                self.completed_datetime = timezone.now()
        
        super().save(*args, **kwargs)

    @property
    def completion_percentage(self):
        if self.total_work == 0:
            return 0
        return round((self.completed_work / self.total_work) * 100, 1)

    @property
    def duration(self):
        """Calculate duration from start to completion"""
        if not self.start_datetime:
            return None
        
        end_time = self.completed_datetime if self.completed_datetime else None
        if not end_time:
            return None
        
        duration = end_time - self.start_datetime
        return duration

    @property
    def duration_display(self):
        """Return formatted duration string"""
        if not self.duration:
            return "—"
        
        total_seconds = int(self.duration.total_seconds())
        
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    @property
    def duration_hours(self):
        """Return total duration in hours (float)"""
        if not self.duration:
            return None
        return round(self.duration.total_seconds() / 3600, 2)

    def __str__(self):
        return f"{self.task_title} → {self.assigned_to}"
