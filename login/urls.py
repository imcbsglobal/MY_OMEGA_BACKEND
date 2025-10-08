from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.superuser_id_login, name='superuser-id-login'),
    path('token/refresh/', views.refresh_token, name='token-refresh'),
    path('me/', views.me, name='me'),
]
