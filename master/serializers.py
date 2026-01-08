from rest_framework import serializers
from .models import LeaveMaster

class LeaveMasterSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
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

class LeaveMasterCreateSerializer(serializers.ModelSerializer):
    def validate(self, data):
        category = data.get('category')
        leave_date = data.get('leave_date')

        if category in ['special', 'mandatory_holiday'] and not leave_date:
            raise serializers.ValidationError({
                'leave_date': 'Date is required for Special Leave and Mandatory Holiday'
            })

        return data

    class Meta:
        model = LeaveMaster
        fields = [
            'leave_name',
            'leave_date',
            'payment_status',
            'category',
            'is_active'
        ]
