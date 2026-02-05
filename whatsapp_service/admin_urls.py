# whatsapp_service/admin_urls.py
"""
URL Configuration for WhatsApp Admin Panel

This module routes admin panel API requests to the appropriate ViewSets.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# ✅ CORRECT: Import from admin_views (not public_admin_views)
from .admin_views import (
    WhatsAppConfigurationViewSet,
    AdminNumberViewSet,
    MessageTemplateViewSet
)

# Setup DRF router
router = DefaultRouter()

# Register ViewSets with routes
router.register(r'configurations', WhatsAppConfigurationViewSet, basename='whatsapp-config')
router.register(r'admin-numbers', AdminNumberViewSet, basename='admin-number')
router.register(r'templates', MessageTemplateViewSet, basename='message-template')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]