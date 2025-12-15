# login/urls.py
from django.urls import path
from . import views
from .views import login_view, token_refresh_view

urlpatterns = [
    path('login/', views.login_view, name='api-login'),
    path('protected/', views.protected_view, name='api-protected'),
    path('token-login/', views.token_login_view, name='api-token-login'),
    # path('login/', login_view, name='login'),
    path('token/refresh/', token_refresh_view, name='token_refresh'),
]