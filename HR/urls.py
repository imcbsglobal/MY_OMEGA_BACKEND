# HR/urls.py - Apply menu-based permissions
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AttendanceViewSet, HolidayViewSet, LeaveRequestViewSet,
    LateRequestViewSet, EarlyRequestViewSet,
    reverse_geocode, reverse_geocode_bigdata
)

# Create router
router = DefaultRouter()

# Register viewsets with menu_key set
# The HasMenuAccess permission will check for 'attendance' menu access
attendance_viewset = AttendanceViewSet
attendance_viewset.menu_key = 'attendance'
router.register(r'attendance', attendance_viewset, basename='attendance')

holiday_viewset = HolidayViewSet
holiday_viewset.menu_key = 'attendance'
router.register(r'holidays', holiday_viewset, basename='holiday')

leave_viewset = LeaveRequestViewSet
leave_viewset.menu_key = 'attendance'
router.register(r'leave-requests', leave_viewset, basename='leave-request')


late_viewset = LateRequestViewSet
late_viewset.menu_key = 'attendance'
router.register(r'late-requests', late_viewset, basename='late-request')

early_viewset = EarlyRequestViewSet
early_viewset.menu_key = 'attendance'
router.register(r'early-requests', early_viewset, basename='early-request')

urlpatterns = [
    path('', include(router.urls)),
    path('reverse-geocode/', reverse_geocode, name='reverse-geocode'),
    path('reverse-geocode-bigdata/', reverse_geocode_bigdata, name='reverse-geocode-bigdata'),
]