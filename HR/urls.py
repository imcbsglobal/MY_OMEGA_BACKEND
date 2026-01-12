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

# NOTES:
# Break endpoints are automatically registered via @action decorators in AttendanceViewSet:
#   - GET  /api/hr/attendance/active_break/
#   - POST /api/hr/attendance/start_break/
#   - POST /api/hr/attendance/end_break/
#   - GET  /api/hr/attendance/today_breaks/
#   - GET  /api/hr/attendance/break_summary/
#
# DO NOT add them again here as standalone paths - this causes 405/404 errors!

