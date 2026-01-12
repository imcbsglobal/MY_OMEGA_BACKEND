# ============================================================================
# FILE 6: whatsapp_service/serializers.py
# ============================================================================

from rest_framework import serializers


class SendMessageSerializer(serializers.Serializer):
    to = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField()