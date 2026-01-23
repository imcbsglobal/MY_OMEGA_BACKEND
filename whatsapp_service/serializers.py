# ============================================================================
# FILE 6: whatsapp_service/serializers.py
# ============================================================================

from rest_framework import serializers


class SendMessageSerializer(serializers.Serializer):
    to = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField()



# whatsapp_service/admin_serializers.py
from rest_framework import serializers
from .models import WhatsAppConfiguration, AdminNumber, MessageTemplate


class WhatsAppConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppConfiguration
        fields = [
            'id',
            'provider',
            'api_url',
            'api_secret',
            'account_id',
            'default_priority',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_default_priority(self, value):
        if not 1 <= value <= 10:
            raise serializers.ValidationError("Priority must be between 1 and 10")
        return value


class AdminNumberSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = AdminNumber
        fields = [
            'id',
            'name',
            'phone_number',
            'role',
            'role_display',
            'is_active',
            'is_api_sender',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_phone_number(self, value):
        # Ensure phone number starts with +
        if not value.startswith('+'):
            if value.isdigit():
                # Assume Indian number if 10 digits
                if len(value) == 10:
                    value = '+91' + value
                else:
                    value = '+' + value
        return value


class MessageTemplateSerializer(serializers.ModelSerializer):
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    recipient_type_display = serializers.CharField(source='get_recipient_type_display', read_only=True)
    available_variables = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageTemplate
        fields = [
            'id',
            'template_type',
            'template_type_display',
            'recipient_type',
            'recipient_type_display',
            'template_text',
            'is_active',
            'available_variables',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_available_variables(self, obj):
        """Return available variables based on template type"""
        common_vars = ['{employee_name}', '{date}', '{time}']
        
        variable_map = {
            'punch_in': common_vars + ['{action}', '{location}'],
            'punch_out': common_vars + ['{action}', '{location}'],
            'leave_request': common_vars + ['{leave_type}', '{days}', '{reason}', '{from_date}', '{to_date}'],
            'leave_approval': common_vars + ['{leave_type}', '{days}', '{reason}', '{status}', '{approver_name}'],
            'leave_rejection': common_vars + ['{leave_type}', '{days}', '{reason}', '{status}', '{approver_name}'],
            'late_request': common_vars + ['{reason}', '{late_by}'],
            'late_approval': common_vars + ['{reason}', '{late_by}', '{status}', '{approver_name}'],
            'late_rejection': common_vars + ['{reason}', '{late_by}', '{status}', '{approver_name}'],
            'early_request': common_vars + ['{reason}', '{early_by}'],
            'early_approval': common_vars + ['{reason}', '{early_by}', '{status}', '{approver_name}'],
            'early_rejection': common_vars + ['{reason}', '{early_by}', '{status}', '{approver_name}'],
            'generic_notification': common_vars + ['{message}'],
        }
        
        return variable_map.get(obj.template_type, common_vars)

