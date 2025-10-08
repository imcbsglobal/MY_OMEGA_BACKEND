# login/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),

    path('refresh/', views.refresh_token_view, name='refresh-token'),
    path('protected/', views.protected_view, name='protected'),
    path('test/', views.test_view, name='test'),
]