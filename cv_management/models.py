from django.db import models
from User.models import AppUser

# Create your models here.
class UserCvData(models.Model) :
    name = models.CharField(max_length=30)
    created_at = models.DateField(auto_now_add=True)
    updated_by = models.ForeignKey(AppUser, verbose_name=("updated User"), on_delete=models.CASCADE)

    def __str__(self):
        return self.name