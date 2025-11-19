from django.db import models
from User.models import AppUser


class SalaryCertificate(models.Model):

    employee = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='salary_certificates',
        verbose_name='Employee'
    )

    salary = models.DecimalField(
        max_digits=10,decimal_places=2,default=0.00,
        verbose_name="Salary Amount"
    )
    generated_by = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_salary_certificate",
        verbose_name="generated_by"
    )

    issued_date = models.DateField(auto_now_add=True)

    class Meta:
        ordering=['-issued_date']
        verbose_name="SalaryCertificate"
        verbose_name_plural = "Salary Certificates"


 
    def __str__(self):
        return f"Salary Certificate for {self.employee}"


class ExperienceCertificate(models.Model):
    