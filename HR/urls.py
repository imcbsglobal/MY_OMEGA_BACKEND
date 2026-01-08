# HR/urls.py - Complete URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AttendanceViewSet,
    HolidayViewSet,
    LeaveRequestViewSet,
    LeaveMasterViewSet,
    LateRequestViewSet,
    EarlyRequestViewSet,
    reverse_geocode,
    reverse_geocode_bigdata
)

router = DefaultRouter()
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'holidays', HolidayViewSet, basename='holiday')
router.register(r'leave-masters', LeaveMasterViewSet, basename='leave-master')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leave-request')
router.register(r'late-requests', LateRequestViewSet, basename='late-request')
router.register(r'early-requests', EarlyRequestViewSet, basename='early-request')

urlpatterns = [
    path('', include(router.urls)),
    path('reverse-geocode/', reverse_geocode, name='reverse-geocode'),
    path('reverse-geocode-bigdata/', reverse_geocode_bigdata, name='reverse-geocode-bigdata'),
]