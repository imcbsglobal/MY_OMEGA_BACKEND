from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeaveMasterViewSet, AssetMasterViewSet



router = DefaultRouter()
router.register('leaves', LeaveMasterViewSet, basename='leave-master')
router.register('assets', AssetMasterViewSet, basename='asset-master')

urlpatterns = [
    path('', include(router.urls)),
]

