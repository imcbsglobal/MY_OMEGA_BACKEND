from django.db import models
from django.conf import settings
from employee_management.models import Employee
from offer_letter.models import OfferLetter

class SalaryCertificate(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='salary_certificates',
        verbose_name='Employee'
    )

    salary = models.DecimalField(
        max_digits=10,decimal_places=2,default=0.00,
        verbose_name="Salary Amount"
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='employee',
        related_name='experience_certificates'
    )
    offer_letter = models.ForeignKey(
        OfferLetter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='experience_certificates'
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_experience_certificates",
        verbose_name="generated_by"
    )

    #fallback if offer letter not provided
    joining_date = models.DateField(null=True,blank=True)
    issue_date = models.DateField(auto_now_add=True)

    class Meta :
        verbose_name = "Experience certificate"
        verbose_name_plural = "Experience certificate"
    def save(self, *args, **kwargs):
        if self.offer_letter and not self.joining_date:
            # Note: OfferLetter field is 'joining_data' not 'joining_date'
            self.joining_date = getattr(self.offer_letter, 'joining_data', None)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Experience Certificate for {self.employee}"

