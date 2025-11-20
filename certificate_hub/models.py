from django.db import models
from User.models import AppUser
from offer_letter.models import OfferLetter

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
    employee=models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        verbose_name='employee',
        related_name='employee'
    )
    offer_letter = models.ForeignKey(
    OfferLetter,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="Experience Certificate"
    )
    generated_by = models.ForeignKey(
        AppUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_salary_certificate",
        verbose_name="generated_by"
    )

    #fallback if offer letter not provided
    joining_date = models.DateField(null=True,blank=True)
    issue_date = models.DateField(auto_now_add=True)

    class Meta :
        verbose_name = "Experience certificate"
        verbose_name_plural = "Experience certificate"
    def save(self, *args ,**kwargs ):
        if self.offer_letter and not self.joining_date:
            self.joining_date = getattr(self.offer_letter,'joining_date',None)
        super.save(*args , **kwargs)
    def __str__(self):
        return f"Experience Certificate fro {self.employee}"

