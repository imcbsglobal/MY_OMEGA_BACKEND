from django.urls import path
from . import views

urlpatterns = [

    # List and create salary certificates
    path('salary-certificates/', views.salary_certificate_list_create, name='salary-certificate-list-create'),
    
    # Retrieve, update, and delete a specific salary certificate
    path('salary-certificates/<int:pk>/', views.salary_certificate_detail, name='salary-certificate-detail'),
    
    # Get active employees list
    path('employees/', views.employee_list, name='employee-list'),
    
]