from rest_framework import serializers
from .models import LeaveMaster

class LeaveMasterSerializer(serializers.ModelSerializer):
    category_display = serializers.SerializerMethodField()
    payment_status_display = serializers.SerializerMethodField()

    class Meta:
        model = LeaveMaster
        fields = [
            'id',
            'leave_name',
            'leave_date',
            'payment_status',
            'payment_status_display',
            'category',
            'category_display',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_category_display(self, obj):
        try:
            return obj.get_category_display()
        except Exception:
            # fallback if invalid data exists
            return obj.category

    def get_payment_status_display(self, obj):
        try:
            return obj.get_payment_status_display()
        except Exception:
            return obj.payment_status
