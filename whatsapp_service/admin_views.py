# whatsapp_service/admin_views.py
"""
WhatsApp Admin Panel ViewSets - NO AUTHENTICATION VERSION

⚠️  WARNING: This version has NO authentication for development/testing.
    Use only in development. For production, restore proper authentication.

Changes made:
✅ Removed all authentication requirements
✅ Set permissions to AllowAny
✅ Added enhanced error logging
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings
from .models import WhatsAppConfiguration, AdminNumber, MessageTemplate
from .serializers import (
    WhatsAppConfigurationSerializer,
    AdminNumberSerializer,
    MessageTemplateSerializer
)
import logging

logger = logging.getLogger(__name__)


class WhatsAppConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing WhatsApp API configurations.
    
    ⚠️  NO AUTHENTICATION - Development only!
    """
    queryset = WhatsAppConfiguration.objects.all()
    serializer_class = WhatsAppConfigurationSerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Order by active status and creation date"""
        logger.info("📋 Fetching WhatsApp configurations")
        return WhatsAppConfiguration.objects.all().order_by('-is_active', '-created_at')
    
    def create(self, request, *args, **kwargs):
        """Create new configuration with enhanced error handling"""
        logger.info(f"📝 Creating new WhatsApp configuration")
        logger.info(f"Request data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"❌ Validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.perform_create(serializer)
            logger.info(f"✅ Configuration created successfully: ID {serializer.data['id']}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"💥 Error creating configuration: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to create configuration: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def update(self, request, *args, **kwargs):
        """Update existing configuration with enhanced error handling"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        logger.info(f"✏️  Updating configuration ID {instance.id}")
        logger.info(f"Request data: {request.data}")
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if not serializer.is_valid():
            logger.error(f"❌ Validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.perform_update(serializer)
            logger.info(f"✅ Configuration updated successfully: ID {instance.id}")
            return Response(serializer.data)
        except Exception as e:
            logger.exception(f"💥 Error updating configuration: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to update configuration: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
        test_message = request.data.get('test_message', '📱 Test message from WhatsApp Admin Panel')
        
        logger.info(f"🧪 Testing configuration {config.id} with number {test_number}")
        
        if not test_number:
            return Response(
                {'success': False, 'error': 'test_number is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Import here to avoid circular imports
        try:
            from .services.whatsapp_client import send_text, WhatsAppClientError
        except ImportError:
            try:
                from .whatsapp_client import send_text, WhatsAppClientError
            except ImportError:
                logger.error("❌ Could not import WhatsApp client")
                return Response({
                    'success': False,
                    'error': 'WhatsApp client not available'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Store old settings
        old_settings = {
            'api_url': getattr(settings, 'DXING_API_URL', None),
            'secret': getattr(settings, 'DXING_SECRET', None),
            'account': getattr(settings, 'DXING_ACCOUNT', None),
        }
        
        try:
            # Apply test configuration temporarily
            settings.DXING_API_URL = config.api_url
            settings.DXING_SECRET = config.api_secret
            settings.DXING_ACCOUNT = config.account_id
            
            # Try to send test message
            result = send_text(
                test_number, 
                test_message,
                priority=config.default_priority
            )
            
            logger.info(f"✅ Test message sent successfully via config {config.id}")
            
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
            
        except Exception as e:
            logger.error(f"❌ WhatsApp test failed for config {config.id}: {str(e)}")
            return Response(
                {
                    'success': False,
                    'error': str(e),
                    'suggestion': 'Please check your API credentials and try again'
                },
                status=status.HTTP_502_BAD_GATEWAY
            )
        finally:
            # Restore original settings
            settings.DXING_API_URL = old_settings['api_url']
            settings.DXING_SECRET = old_settings['secret']
            settings.DXING_ACCOUNT = old_settings['account']
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate this configuration and deactivate all others.
        
        POST /api/whatsapp/admin/configurations/{id}/activate/
        """
        config = self.get_object()
        
        logger.info(f"⚡ Activating configuration {config.id} ({config.provider})")
        
        try:
            # Deactivate all others
            WhatsAppConfiguration.objects.exclude(id=config.id).update(is_active=False)
            
            # Activate this one
            config.is_active = True
            config.save()
            
            # Update Django settings
            settings.DXING_API_URL = config.api_url
            settings.DXING_SECRET = config.api_secret
            settings.DXING_ACCOUNT = config.account_id
            
            logger.info(f"✅ Activated WhatsApp configuration: {config.id} ({config.provider})")
            
            return Response({
                'success': True,
                'message': f'Configuration activated: {config.provider}',
                'configuration': WhatsAppConfigurationSerializer(config).data
            })
        except Exception as e:
            logger.exception(f"💥 Error activating configuration: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to activate configuration: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def active_config(self, request):
        """
        Get the currently active configuration.
        
        GET /api/whatsapp/admin/configurations/active_config/
        """
        logger.info("🔍 Fetching active configuration")
        
        active = WhatsAppConfiguration.objects.filter(is_active=True).first()
        
        if not active:
            logger.warning("⚠️  No active configuration found")
            return Response({
                'success': False,
                'message': 'No active configuration found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        logger.info(f"✅ Active config: {active.provider} (ID: {active.id})")
        
        return Response({
            'success': True,
            'configuration': WhatsAppConfigurationSerializer(active).data
        })


class AdminNumberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing admin phone numbers.
    
    ⚠️  NO AUTHENTICATION - Development only!
    """
    queryset = AdminNumber.objects.all()
    serializer_class = AdminNumberSerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Filter and order admin numbers"""
        logger.info("📋 Fetching admin numbers")
        
        queryset = AdminNumber.objects.all()
        
        # Filter by role if provided
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
            logger.info(f"🔍 Filtering by role: {role}")
        
        # Filter active only if requested
        active_only = self.request.query_params.get('active_only', None)
        if active_only == 'true':
            queryset = queryset.filter(is_active=True)
            logger.info("🔍 Filtering active only")
        
        return queryset.order_by('role', 'name')
    
    def create(self, request, *args, **kwargs):
        """Create admin number with enhanced error handling"""
        logger.info(f"📝 Creating new admin number")
        logger.info(f"Request data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"❌ Validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.perform_create(serializer)
            logger.info(f"✅ Admin number created successfully: {serializer.data['name']}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"💥 Error creating admin number: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to create admin number: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def send_test(self, request, pk=None):
        """
        Send a test WhatsApp message to this admin number.
        
        POST /api/whatsapp/admin/admin-numbers/{id}/send_test/
        """
        admin_number = self.get_object()
        test_message = request.data.get(
            'test_message',
            f'📱 Test message for {admin_number.name} from WhatsApp Admin Panel'
        )
        
        logger.info(f"🧪 Sending test message to {admin_number.name} ({admin_number.phone_number})")
        
        try:
            from .utils import send_whatsapp_notification
            
            result = send_whatsapp_notification(admin_number.phone_number, test_message)
            
            if result:
                logger.info(f"✅ Test message sent to {admin_number.name}")
                return Response({
                    'success': True,
                    'message': f'Test message sent to {admin_number.name}',
                    'result': result
                })
            else:
                logger.error(f"❌ Failed to send test to {admin_number.name}")
                return Response({
                    'success': False,
                    'error': 'Failed to send test message'
                }, status=status.HTTP_502_BAD_GATEWAY)
                
        except Exception as e:
            logger.exception(f"💥 Error sending test to {admin_number.phone_number}: {str(e)}")
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
        logger.info("📊 Fetching admin numbers grouped by role")
        
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
        
        logger.info(f"✅ Found {len(result)} roles with admin numbers")
        
        return Response({
            'success': True,
            'roles': result
        })


class MessageTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing message templates.
    
    ⚠️  NO AUTHENTICATION - Development only!
    """
    queryset = MessageTemplate.objects.all()
    serializer_class = MessageTemplateSerializer
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """Filter templates"""
        logger.info("📋 Fetching message templates")
        
        queryset = MessageTemplate.objects.all()
        
        # Filter by type if provided
        template_type = self.request.query_params.get('type', None)
        if template_type:
            queryset = queryset.filter(template_type=template_type)
            logger.info(f"🔍 Filtering by type: {template_type}")
        
        # Filter active only if requested
        active_only = self.request.query_params.get('active_only', None)
        if active_only == 'true':
            queryset = queryset.filter(is_active=True)
            logger.info("🔍 Filtering active only")
        
        return queryset.order_by('template_type')
    
    def create(self, request, *args, **kwargs):
        """Create template with enhanced error handling"""
        logger.info(f"📝 Creating new template")
        logger.info(f"Request data: {request.data}")
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"❌ Validation failed: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.perform_create(serializer)
            logger.info(f"✅ Template created successfully")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"💥 Error creating template: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to create template: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """
        Preview a template with sample data.
        
        POST /api/whatsapp/admin/templates/{id}/preview/
        """
        template = self.get_object()
        context = request.data.get('context', {})
        
        logger.info(f"👁️  Previewing template {template.template_type}")
        
        # Provide default sample data
        default_context = {
            'employee_name': 'John Doe',
            'date': '27 Jan 2026',
            'time': '09:30 AM',
            'location': 'Office',
            'action': 'PUNCH IN',
            'leave_type': 'Casual Leave',
            'days': '2',
            'reason': 'Personal work',
            'status': 'Approved',
            'approver_name': 'Manager',
            'from_date': '28 Jan 2026',
            'to_date': '29 Jan 2026',
            'late_by': '15 minutes',
            'early_by': '30 minutes',
            'message': 'Sample notification message'
        }
        
        full_context = {**default_context, **context}
        
        try:
            rendered = template.render(**full_context)
            logger.info(f"✅ Template {template.template_type} rendered successfully")
            
            return Response({
                'success': True,
                'template_type': template.get_template_type_display(),
                'preview': rendered,
                'context_used': full_context
            })
        except Exception as e:
            logger.error(f"❌ Error rendering template {template.template_type}: {e}")
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
        logger.info("🔄 Resetting templates to defaults")
        
        try:
            self._create_default_templates()
            logger.info("✅ Templates reset successfully")
            
            return Response({
                'success': True,
                'message': 'All templates reset to defaults'
            })
        except Exception as e:
            logger.exception(f"💥 Error resetting templates: {str(e)}")
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
                'template_text': '📍 Attendance Alert\n\nEmployee: {employee_name}\nAction: PUNCH IN\nTime: {time}\nDate: {date}\nLocation: {location}\n\nThank you!',
                'is_active': True
            },
            {
                'template_type': 'punch_out',
                'recipient_type': 'both',
                'template_text': '📍 Attendance Alert\n\nEmployee: {employee_name}\nAction: PUNCH OUT\nTime: {time}\nDate: {date}\nLocation: {location}\n\nThank you!',
                'is_active': True
            },
            {
                'template_type': 'leave_request',
                'recipient_type': 'both',
                'template_text': '📋 Leave Request Submitted\n\nEmployee: {employee_name}\nType: {leave_type}\nFrom: {from_date}\nTo: {to_date}\nDays: {days}\nReason: {reason}\n\nStatus: Pending Approval',
                'is_active': True
            },
            {
                'template_type': 'leave_approval',
                'recipient_type': 'employee',
                'template_text': '✅ Leave Request APPROVED\n\nEmployee: {employee_name}\nType: {leave_type}\nFrom: {from_date}\nTo: {to_date}\nDays: {days}\n\nApproved by: {approver_name}',
                'is_active': True
            },
            {
                'template_type': 'leave_rejection',
                'recipient_type': 'employee',
                'template_text': '❌ Leave Request REJECTED\n\nEmployee: {employee_name}\nType: {leave_type}\nFrom: {from_date}\nTo: {to_date}\nDays: {days}\n\nRejected by: {approver_name}\nReason: {reason}',
                'is_active': True
            },
        ]
        
        for template_data in defaults:
            MessageTemplate.objects.update_or_create(
                template_type=template_data['template_type'],
                defaults=template_data
            )
            logger.info(f"✅ Updated template: {template_data['template_type']}")