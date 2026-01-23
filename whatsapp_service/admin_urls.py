
# whatsapp_service/admin_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WhatsAppConfigurationViewSet,
    AdminNumberViewSet,
    MessageTemplateViewSet
)

router = DefaultRouter()
router.register(r'configurations', WhatsAppConfigurationViewSet, basename='whatsapp-config')
router.register(r'admin-numbers', AdminNumberViewSet, basename='admin-number')
router.register(r'templates', MessageTemplateViewSet, basename='message-template')

urlpatterns = [
    path('', include(router.urls)),
]
