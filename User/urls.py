
# User/urls.py - COMPLETE VERSION
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import AppUserViewSet, login_view, logout_view

router = DefaultRouter()
router.register(r'users', AppUserViewSet, basename='appuser')

urlpatterns = [
    # Authentication endpoints
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User CRUD endpoints (from router)
    path('', include(router.urls)),
]