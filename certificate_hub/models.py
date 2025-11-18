from django.db import models
from cv_management.models import UserCvData
from User.models import AppUser


class SalaryCertificate(models.Model):

    employee = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='salary',
        verbose_name='employee'
    )

    salary = models.DecimalField(
        max_digits=10,decimal_places=2,default=0.00
    )
    generated_by = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="generated_by",
        verbose_name="generated_by"
    )
    issued_date = models.DateField(auto_now_add=True)

    class Meta:
        ordering=['-issued_date']
        verbose_name="SalaryCertificate"

    def __str__(self):
        return f"SalaryCertificate - {self.employee} )"


