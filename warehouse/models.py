from django.db import models
from django.conf import settings


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Warehouse Task'
        verbose_name_plural = 'Warehouse Tasks'

    def save(self, *args, **kwargs):
        # Auto-update status based on completed_work
        if self.completed_work >= self.total_work and self.total_work > 0:
            self.status = self.STATUS_COMPLETED
        super().save(*args, **kwargs)

    @property
    def completion_percentage(self):
        if self.total_work == 0:
            return 0
        return round((self.completed_work / self.total_work) * 100, 1)

    def __str__(self):
        return f"{self.task_title} → {self.assigned_to}"
