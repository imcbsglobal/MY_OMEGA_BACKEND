# HR/urls.py - FIXED VERSION (No Duplicates)

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AttendanceViewSet,
    HolidayViewSet,
    LeaveRequestViewSet,
    LeaveMasterViewSet,
    LateRequestViewSet,
    EarlyRequestViewSet,
    get_office_geofence_info,
    reverse_geocode,
    reverse_geocode_bigdata
)

router = DefaultRouter()

# Register all viewsets - MAKE SURE EACH BASENAME IS UNIQUE
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'holidays', HolidayViewSet, basename='holiday')
router.register(r'leave-masters', LeaveMasterViewSet, basename='leave-master')

# ✅ ONLY ONE 'leave' registration - remove any duplicates!
router.register(r'leave', LeaveRequestViewSet, basename='leave')

router.register(r'late-requests', LateRequestViewSet, basename='late-request')
router.register(r'early-requests', EarlyRequestViewSet, basename='early-request')

urlpatterns = [
    path('', include(router.urls)),
    path('reverse-geocode/', reverse_geocode, name='reverse-geocode'),
    path('reverse-geocode-bigdata/', reverse_geocode_bigdata, name='reverse-geocode-bigdata'),
    path('geofence-info/', get_office_geofence_info, name='geofence-info'),
]

# ================================================================
# IMPORTANT: Each router.register() basename must be UNIQUE
# ================================================================
# ✅ CORRECT - One registration per viewset
# ❌ WRONG - Do NOT have multiple lines with same basename
#
# Example of WRONG (causes error):
#   router.register(r'leave', LeaveRequestViewSet, basename='leave')
#   router.register(r'leave', LeaveRequestViewSet, basename='leave')  # DUPLICATE!
# ================================================================