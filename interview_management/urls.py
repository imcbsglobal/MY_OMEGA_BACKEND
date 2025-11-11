from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InterviewManagementViewSet

router = DefaultRouter()
router.register(r'', InterviewManagementViewSet, basename='interview')

urlpatterns = [
    path('', include(router.urls)),
]
