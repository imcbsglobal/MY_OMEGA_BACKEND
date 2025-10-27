# login/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='api-login'),
    path('refresh/', views.refresh_token_view, name='api-refresh'),
    path('protected/', views.protected_view, name='api-protected'),
    # NEW: paste an access/refresh token to login
    path('token-login/', views.token_login_view, name='api-token-login'),
]
