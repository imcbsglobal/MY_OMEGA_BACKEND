# HR/urls.py - UPDATED with Office Configuration endpoints

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
from .views_office_config import (
    OfficeLocationViewSet,
    get_office_geofence_info,
    update_geofence_radius
)

router = DefaultRouter()

# Existing registrations
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'holidays', HolidayViewSet, basename='holiday')
router.register(r'leave-masters', LeaveMasterViewSet, basename='leave-master')
router.register(r'leave', LeaveRequestViewSet, basename='leave')
router.register(r'late-requests', LateRequestViewSet, basename='late-request')
router.register(r'early-requests', EarlyRequestViewSet, basename='early-request')

# NEW: Office configuration endpoints (Admin only)
router.register(r'office-locations', OfficeLocationViewSet, basename='office-location')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Geocoding endpoints
    path('reverse-geocode/', reverse_geocode, name='reverse-geocode'),
    path('reverse-geocode-bigdata/', reverse_geocode_bigdata, name='reverse-geocode-bigdata'),
    
    # Office geofence info (available to all users)
    path('geofence-info/', get_office_geofence_info, name='geofence-info'),
    
    # Quick radius update endpoint (admin only)
    path('update-geofence-radius/', update_geofence_radius, name='update-geofence-radius'),
]

# ================================================================
# Office Configuration API Endpoints:
# ================================================================
# 
# 1. GET    /api/hr/office-locations/
#    - List all office locations (Admin)
# 
# 2. POST   /api/hr/office-locations/
#    - Create new office location (Admin)
#    Body: { name, address, latitude, longitude, geofence_radius_meters }
# 
# 3. GET    /api/hr/office-locations/{id}/
#    - Get specific office location details (Admin)
# 
# 4. PUT    /api/hr/office-locations/{id}/
#    - Update office location (Admin)
# 
# 5. DELETE /api/hr/office-locations/{id}/
#    - Delete office location (Admin)
# 
# 6. GET    /api/hr/office-locations/active/
#    - Get currently active office location (Admin)
# 
# 7. POST   /api/hr/office-locations/{id}/set-active/
#    - Set specific office as active (Admin)
# 
# 8. POST   /api/hr/office-locations/{id}/test-location/
#    - Test a location against geofence (Admin)
#    Body: { latitude, longitude }
# 
# 9. POST   /api/hr/office-locations/detect-my-location/
#    - Create office using admin's current GPS location (Admin)
#    Body: { name, address, latitude, longitude, geofence_radius_meters, gps_accuracy_meters }
# 
# 10. GET   /api/hr/geofence-info/
#     - Get active office info for display (All authenticated users)
# 
# 11. POST  /api/hr/update-geofence-radius/
#     - Quick update of radius only (Admin)
#     Body: { radius_meters }
# 
# ================================================================