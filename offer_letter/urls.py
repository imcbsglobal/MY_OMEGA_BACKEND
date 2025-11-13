from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OfferLetterViewSet

router = DefaultRouter()
router.register(r'', OfferLetterViewSet, basename='offer-letter')

urlpatterns = [
    path('', include(router.urls)),
]