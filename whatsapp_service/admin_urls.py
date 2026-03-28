# whatsapp_service/admin_urls.py
"""
URL Configuration for WhatsApp Admin Panel
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .admin_views import (
    WhatsAppConfigurationViewSet,
    AdminNumberViewSet,
    MessageTemplateViewSet,
    SendMessageView,
)

router = DefaultRouter()
router.register(r'configurations', WhatsAppConfigurationViewSet, basename='whatsapp-config')
router.register(r'admin-numbers', AdminNumberViewSet, basename='admin-number')
router.register(r'templates', MessageTemplateViewSet, basename='message-template')

urlpatterns = [
    path('', include(router.urls)),
    # Manual send from admin portal
    path('send/', SendMessageView.as_view(), name='admin-send-message'),
]