# ============================================================================
# FILE 7: whatsapp_service/urls.py
# ============================================================================

from django.urls import path
from .views import PunchInView, PunchOutView, GenericRequestView


urlpatterns = [
    path('punchin/', PunchInView.as_view(), name='punchin'),
    path('punchout/', PunchOutView.as_view(), name='punchout'),
    path('request/', GenericRequestView.as_view(), name='whatsapp_request'),
]