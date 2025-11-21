from django.urls import path
from . import views

urlpatterns = [

    # List and create salary certificates
    path('salary-certificates/', views.salary_certificate_list_create, name='salary-certificate-list-create'),
    
    # Retrieve, update, and delete a specific salary certificate
    path('salary-certificates/<int:pk>/', views.salary_certificate_detail, name='salary-certificate-detail'),
    
    # Get active employees list
    path('employees/', views.employee_list, name='employee-list'),
    
    # List and create experience certificates
    path('experience-certificates/', views.experience_certificate_list_create, name='experience-certificate-list-create'),
    
    # Retrieve, update, and delete a specific experience certificate
    path('experience-certificates/<int:pk>/', views.experience_certificate_detail, name='experience-certificate-detail')

]