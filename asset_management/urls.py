from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AssetViewSet, employees_lookup

app_name = 'asset-management'

router = DefaultRouter()
router.register(r'assets', AssetViewSet, basename='asset')

urlpatterns = [
    path('', include(router.urls)),
    path('employees/', employees_lookup, name='asset-employees'),
]
