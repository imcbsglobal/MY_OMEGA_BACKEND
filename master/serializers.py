from rest_framework import serializers
from .models import LeaveMaster, AssetMaster

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



class LeaveMasterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveMaster
        fields = ['leave_name', 'leave_date', 'category', 'payment_status', 'is_active', 'description']


class AssetMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetMaster
        fields = [
            'id',
            'asset_name',
            'asset_id',
            'asset_category',
            'serial_number',
            'is_active',
            'description',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_asset_id(self, value):
        queryset = AssetMaster.objects.filter(asset_id=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('An asset with this ID already exists.')
        return value
