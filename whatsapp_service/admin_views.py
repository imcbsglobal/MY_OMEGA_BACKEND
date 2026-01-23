# whatsapp_service/admin_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.conf import settings
from .models import WhatsAppConfiguration, AdminNumber, MessageTemplate
from .serializers import (
    WhatsAppConfigurationSerializer,
    AdminNumberSerializer,
    MessageTemplateSerializer
)
from .services.whatsapp_client import send_text, WhatsAppClientError
import logging

logger = logging.getLogger(__name__)


class WhatsAppConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing WhatsApp API configurations.
    Supports CRUD operations and testing configurations.
    """
    queryset = WhatsAppConfiguration.objects.all()
    serializer_class = WhatsAppConfigurationSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Order by active status and creation date"""
        return WhatsAppConfiguration.objects.all().order_by('-is_active', '-created_at')
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        Test the WhatsApp configuration by sending a test message.
        
        POST /api/whatsapp/admin/configurations/{id}/test_connection/
        Body: {
            "test_number": "+918281561081",
            "test_message": "Test message from admin panel"
        }
        """
        config = self.get_object()
        test_number = request.data.get('test_number')
        test_message = request.data.get('test_message', '🔔 Test message from WhatsApp Admin Panel')
        
        if not test_number:
            return Response(
                {'success': False, 'error': 'test_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Temporarily update settings to use this configuration
        old_settings = {
            'provider': getattr(settings, 'WHATSAPP_PROVIDER', None),
            'api_url': getattr(settings, 'DXING_API_URL', None),
            'secret': getattr(settings, 'DXING_SECRET', None),
            'account': getattr(settings, 'DXING_ACCOUNT', None),
        }
        
        try:
            # Apply test configuration
            settings.WHATSAPP_PROVIDER = config.provider
            settings.DXING_API_URL = config.api_url
            settings.DXING_SECRET = config.api_secret
            settings.DXING_ACCOUNT = config.account_id
            
            # Try to send test message
            result = send_text(
                test_number, 
                test_message,
                priority=config.default_priority
            )
            
            return Response({
                'success': True,
                'message': 'Test message sent successfully',
                'result': result,
                'configuration': {
                    'id': config.id,
                    'provider': config.provider,
                    'is_active': config.is_active
                }
            })
            
        except WhatsAppClientError as e:
            logger.error(f"WhatsApp test failed for config {config.id}: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': str(e),
                    'suggestion': 'Please check your API credentials and try again'
                },
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            logger.exception(f"Unexpected error testing config {config.id}: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': f'Unexpected error: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Restore original settings
            settings.WHATSAPP_PROVIDER = old_settings['provider']
            settings.DXING_API_URL = old_settings['api_url']
            settings.DXING_SECRET = old_settings['secret']
            settings.DXING_ACCOUNT = old_settings['account']
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate this configuration and deactivate all others.
        Also updates Django settings.
        
        POST /api/whatsapp/admin/configurations/{id}/activate/
        """
        config = self.get_object()
        
        # Deactivate all others
        WhatsAppConfiguration.objects.exclude(id=config.id).update(is_active=False)
        
        # Activate this one
        config.is_active = True
        config.save()
        
        # Update Django settings
        settings.WHATSAPP_PROVIDER = config.provider
        settings.DXING_API_URL = config.api_url
        settings.DXING_SECRET = config.api_secret
        settings.DXING_ACCOUNT = config.account_id
        
        logger.info(f"Activated WhatsApp configuration: {config.id} ({config.provider})")
        
        return Response({
            'success': True,
            'message': f'Configuration activated: {config.provider}',
            'configuration': WhatsAppConfigurationSerializer(config).data
        })
    
    @action(detail=False, methods=['get'])
    def active_config(self, request):
        """
        Get the currently active configuration.
        
        GET /api/whatsapp/admin/configurations/active_config/
        """
        active = WhatsAppConfiguration.objects.filter(is_active=True).first()
        
        if not active:
            return Response({
                'success': False,
                'message': 'No active configuration found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'configuration': WhatsAppConfigurationSerializer(active).data
        })


class AdminNumberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing admin phone numbers.
    """
    queryset = AdminNumber.objects.all()
    serializer_class = AdminNumberSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Filter and order admin numbers"""
        queryset = AdminNumber.objects.all()
        
        # Filter by role if provided
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter active only if requested
        active_only = self.request.query_params.get('active_only', None)
        if active_only == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('role', 'name')
    
    @action(detail=True, methods=['post'])
    def send_test(self, request, pk=None):
        """
        Send a test message to this admin number.
        
        POST /api/whatsapp/admin/admin-numbers/{id}/send_test/
        Body: {
            "message": "Test message"  # Optional
        }
        """
        admin_number = self.get_object()
        test_message = request.data.get(
            'message',
            f'🔔 Test notification for {admin_number.name}'
        )
        
        try:
            from .utils import send_whatsapp_notification
            
            result = send_whatsapp_notification(admin_number.phone_number, test_message)
            
            if result:
                return Response({
                    'success': True,
                    'message': f'Test message sent to {admin_number.name}',
                    'result': result
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Failed to send test message'
                }, status=status.HTTP_502_BAD_GATEWAY)
                
        except Exception as e:
            logger.exception(f"Error sending test to {admin_number.phone_number}: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def by_role(self, request):
        """
        Get admin numbers grouped by role.
        
        GET /api/whatsapp/admin/admin-numbers/by_role/
        """
        from django.db.models import Count
        
        roles = AdminNumber.objects.filter(is_active=True).values(
            'role'
        ).annotate(
            count=Count('id')
        ).order_by('role')
        
        result = {}
        for role_data in roles:
            role = role_data['role']
            numbers = AdminNumber.objects.filter(
                role=role,
                is_active=True
            ).values('id', 'name', 'phone_number')
            result[role] = list(numbers)
        
        return Response({
            'success': True,
            'roles': result
        })


class MessageTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing message templates.
    """
    queryset = MessageTemplate.objects.all()
    serializer_class = MessageTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Filter templates"""
        queryset = MessageTemplate.objects.all()
        
        # Filter by type if provided
        template_type = self.request.query_params.get('type', None)
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        
        # Filter active only if requested
        active_only = self.request.query_params.get('active_only', None)
        if active_only == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('template_type')
    
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """
        Preview a template with sample data.
        
        POST /api/whatsapp/admin/templates/{id}/preview/
        Body: {
            "context": {
                "employee_name": "John Doe",
                "date": "20 Jan 2026",
                ...
            }
        }
        """
        template = self.get_object()
        context = request.data.get('context', {})
        
        # Provide default sample data if not provided
        default_context = {
            'employee_name': 'John Doe',
            'date': '20 Jan 2026',
            'time': '09:30 AM',
            'location': 'Office',
            'action': 'PUNCH IN',
            'leave_type': 'Casual Leave',
            'days': '2',
            'reason': 'Personal work',
            'status': 'Approved',
            'approver_name': 'Manager',
            'from_date': '21 Jan 2026',
            'to_date': '22 Jan 2026',
            'late_by': '15 minutes',
            'early_by': '30 minutes',
            'message': 'Sample notification message'
        }
        
        # Merge provided context with defaults
        full_context = {**default_context, **context}
        
        try:
            rendered = template.render(**full_context)
            return Response({
                'success': True,
                'template_type': template.get_template_type_display(),
                'preview': rendered,
                'context_used': full_context
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error rendering template: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def reset_defaults(self, request):
        """
        Reset all templates to default values.
        
        POST /api/whatsapp/admin/templates/reset_defaults/
        """
        try:
            self._create_default_templates()
            return Response({
                'success': True,
                'message': 'All templates reset to defaults'
            })
        except Exception as e:
            logger.exception(f"Error resetting templates: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _create_default_templates(self):
        """Create or update default templates"""
        defaults = [
            {
                'template_type': 'punch_in',
                'recipient_type': 'both',
                'template_text': '🔔 Attendance Alert\n\nEmployee: {employee_name}\nAction: PUNCH IN\nTime: {time}\nDate: {date}\nLocation: {location}\n\nThank you!'
            },
            {
                'template_type': 'punch_out',
                'recipient_type': 'both',
                'template_text': '🔔 Attendance Alert\n\nEmployee: {employee_name}\nAction: PUNCH OUT\nTime: {time}\nDate: {date}\nLocation: {location}\n\nThank you!'
            },
            {
                'template_type': 'leave_request',
                'recipient_type': 'both',
                'template_text': '📋 Leave Request Submitted\n\nEmployee: {employee_name}\nType: {leave_type}\nFrom: {from_date}\nTo: {to_date}\nDays: {days}\nReason: {reason}\n\nStatus: Pending Approval'
            },
            {
                'template_type': 'leave_approval',
                'recipient_type': 'employee',
                'template_text': '✅ Leave Request APPROVED\n\nEmployee: {employee_name}\nType: {leave_type}\nFrom: {from_date}\nTo: {to_date}\nDays: {days}\n\nApproved by: {approver_name}'
            },
            {
                'template_type': 'leave_rejection',
                'recipient_type': 'employee',
                'template_text': '❌ Leave Request REJECTED\n\nEmployee: {employee_name}\nType: {leave_type}\nFrom: {from_date}\nTo: {to_date}\nDays: {days}\n\nRejected by: {approver_name}\nReason: {reason}'
            },
        ]
        
        for template_data in defaults:
            MessageTemplate.objects.update_or_create(
                template_type=template_data['template_type'],
                defaults=template_data
            )