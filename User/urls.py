# urls.py (app-level)
from django.urls import path
from .views import users, user_detail

urlpatterns = [
    path('users/', users, name='users-list-create'),
    path('users/<int:pk>/', user_detail, name='users-detail'),
]

