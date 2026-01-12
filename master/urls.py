from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeaveMasterViewSet



router = DefaultRouter()
router.register('leaves', LeaveMasterViewSet, basename='leave-master')

urlpatterns = [
    path('', include(router.urls)),
]

