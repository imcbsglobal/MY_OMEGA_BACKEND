# HR/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet, HolidayViewSet, LeaveRequestViewSet

router = DefaultRouter()
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'holidays', HolidayViewSet, basename='holiday')
router.register(r'leave-requests', LeaveRequestViewSet, basename='leave-request')

urlpatterns = [
    path('', include(router.urls)),
]
