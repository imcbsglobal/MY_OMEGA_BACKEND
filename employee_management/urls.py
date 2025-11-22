from django.urls import path
from . import views

app_name = 'employee_management'

urlpatterns = [
    path('employees/', views.EmployeeListAPIView.as_view(), name='employee-list'),
    path('employees/sidebar/', views.employees_sidebar, name='employees-sidebar'),
    path('employees/<int:pk>/', views.EmployeeDetailAPIView.as_view(), name='employee-detail'),
]
