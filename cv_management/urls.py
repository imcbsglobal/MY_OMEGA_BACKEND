from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserCvDataViewSet, JobTitleViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'cvs', UserCvDataViewSet, basename='usercvdata')
router.register(r'job-titles', JobTitleViewSet, basename='jobtitle')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]