from django.urls import path
from . import views

urlpatterns = [
    path('assign/', views.assign_task, name='warehouse-assign-task'),
    path('my-tasks/', views.my_tasks, name='warehouse-my-tasks'),
    path('update/<int:pk>/', views.update_task, name='warehouse-update-task'),
    path('admin-tasks/', views.admin_tasks, name='warehouse-admin-tasks'),
    path('employees/', views.employee_list, name='warehouse-employee-list'),
]
