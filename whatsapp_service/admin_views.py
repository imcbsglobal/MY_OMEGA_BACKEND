# whatsapp_service/admin_views.py
"""
WhatsApp Admin Panel ViewSets

⚠️  Authentication is set to AllowAny for development.
    In production, replace permission_classes with IsAdminUser or similar.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import WhatsAppConfiguration, AdminNumber, MessageTemplate
from .serializers import (
    WhatsAppConfigurationSerializer,
    AdminNumberSerializer,
    MessageTemplateSerializer,
)
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# WhatsApp Configuration
# ============================================================================

class WhatsAppConfigurationViewSet(viewsets.ModelViewSet):
    """Manage WhatsApp API credentials (one active config at a time)."""

    queryset = WhatsAppConfiguration.objects.all().order_by('-is_active', '-created_at')
    serializer_class = WhatsAppConfigurationSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Config create validation failed: {serializer.errors}")
            return Response(
                {'success': False, 'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"Config create error: {e}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            logger.exception(f"Config update error: {e}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        POST /api/whatsapp/admin/configurations/{id}/activate/
        Activate this config and deactivate all others.
        """
        config = self.get_object()
        WhatsAppConfiguration.objects.exclude(id=config.id).update(is_active=False)
        config.is_active = True
        config.save()
        logger.info(f"Config {config.id} ({config.provider}) activated")
        return Response({
            'success': True,
            'message': f'{config.provider.upper()} configuration activated',
            'configuration': WhatsAppConfigurationSerializer(config).data,
        })

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """
        POST /api/whatsapp/admin/configurations/{id}/test_connection/
        Body: { "test_number": "+918281561081", "test_message": "..." }

        Activates this config temporarily (just for this request) and sends
        a test message using the full database-driven pipeline.
        """
        config = self.get_object()
        test_number = request.data.get('test_number', '').strip()
        test_message = request.data.get(
            'test_message',
            f'📱 Test message from WhatsApp Admin Panel ({config.provider.upper()})'
        )

        if not test_number:
            return Response(
                {'success': False, 'error': 'test_number is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from .services.whatsapp_client import (
                _normalize_number_for_provider,
                WhatsAppClientError,
            )
            import requests as req_lib

            api_url  = config.api_url.rstrip('/')
            secret   = config.api_secret
            account  = config.account_id
            priority = config.default_priority
            provider = config.provider.lower()

            to = _normalize_number_for_provider(test_number, provider)

            payload = {
                'secret': secret,
                'account': account,
                'recipient': to,
                'type': 'text',
                'message': test_message,
                'priority': priority,
            }

            resp = req_lib.post(
                api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=15,
            )
            data = resp.json() if resp.content else {}

            if resp.ok or (isinstance(data, dict) and data.get('status') == 200):
                logger.info(f"Test message sent via config {config.id}")
                return Response({
                    'success': True,
                    'message': 'Test message sent successfully',
                    'result': data,
                })
            else:
                error_msg = data.get('message', resp.text) if isinstance(data, dict) else resp.text
                logger.error(f"Test message failed for config {config.id}: {error_msg}")
                return Response(
                    {'success': False, 'error': error_msg},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        except Exception as e:
            logger.exception(f"test_connection error for config {config.id}: {e}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )


# ============================================================================
# Admin Numbers
# ============================================================================

class AdminNumberViewSet(viewsets.ModelViewSet):
    """Manage admin/HR/manager phone numbers that receive notifications."""

    queryset = AdminNumber.objects.all().order_by('role', 'name')
    serializer_class = AdminNumberSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"AdminNumber create error: {e}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=['get'])
    def by_role(self, request):
        """
        GET /api/whatsapp/admin/admin-numbers/by_role/
        Returns all active numbers grouped by role.
        """
        from django.db.models import Count

        roles = (
            AdminNumber.objects.filter(is_active=True)
            .values('role')
            .annotate(count=Count('id'))
            .order_by('role')
        )

        result = {}
        for role_data in roles:
            role = role_data['role']
            numbers = AdminNumber.objects.filter(
                role=role, is_active=True
            ).values('id', 'name', 'phone_number', 'is_api_sender')
            result[role] = list(numbers)

        return Response({'success': True, 'roles': result})

    @action(detail=False, methods=['get'])
    def active_recipients(self, request):
        """
        GET /api/whatsapp/admin/admin-numbers/active_recipients/
        Returns all numbers that will actually receive notifications.
        """
        numbers = AdminNumber.objects.filter(
            is_active=True, is_api_sender=False
        ).values('id', 'name', 'phone_number', 'role')
        return Response({'success': True, 'recipients': list(numbers), 'count': numbers.count()})


# ============================================================================
# Message Templates
# ============================================================================

DEFAULT_TEMPLATES = [
    {
        'template_type': 'punch_in',
        'recipient_type': 'both',
        'template_text': (
            '📍 *Attendance Alert*\n\n'
            'Employee: {employee_name}\n'
            'Action: PUNCH IN ✅\n'
            'Time: {time}\n'
            'Date: {date}\n'
            'Location: {location}\n\n'
            'Have a productive day! 💼'
        ),
    },
    {
        'template_type': 'punch_out',
        'recipient_type': 'both',
        'template_text': (
            '📍 *Attendance Alert*\n\n'
            'Employee: {employee_name}\n'
            'Action: PUNCH OUT 🔴\n'
            'Time: {time}\n'
            'Date: {date}\n'
            'Location: {location}\n\n'
            'Good work today! 👋'
        ),
    },
    {
        'template_type': 'leave_request',
        'recipient_type': 'admin',
        'template_text': (
            '📋 *Leave Request — Action Required*\n\n'
            'Employee: {employee_name}\n'
            'Leave Type: {leave_type}\n'
            'From: {from_date}\n'
            'To: {to_date}\n'
            'Days: {days}\n'
            'Reason: {reason}\n\n'
            'Status: ⏳ Pending Approval'
        ),
    },
    {
        'template_type': 'leave_approval',
        'recipient_type': 'employee',
        'template_text': (
            '✅ *Leave Request APPROVED*\n\n'
            'Dear {employee_name},\n\n'
            'Your leave request has been approved.\n\n'
            'Leave Type: {leave_type}\n'
            'From: {from_date}\n'
            'To: {to_date}\n'
            'Days: {days}\n\n'
            'Approved by: {approver_name}'
        ),
    },
    {
        'template_type': 'leave_rejection',
        'recipient_type': 'employee',
        'template_text': (
            '❌ *Leave Request REJECTED*\n\n'
            'Dear {employee_name},\n\n'
            'Your leave request has been rejected.\n\n'
            'Leave Type: {leave_type}\n'
            'From: {from_date}\n'
            'To: {to_date}\n'
            'Days: {days}\n'
            'Reason: {reason}\n\n'
            'Rejected by: {approver_name}'
        ),
    },
    {
        'template_type': 'late_request',
        'recipient_type': 'admin',
        'template_text': (
            '⏰ *Late Coming Request*\n\n'
            'Employee: {employee_name}\n'
            'Date: {date}\n'
            'Late By: {late_by}\n'
            'Reason: {reason}\n\n'
            'Status: ⏳ Pending Approval'
        ),
    },
    {
        'template_type': 'late_approval',
        'recipient_type': 'employee',
        'template_text': (
            '✅ *Late Request APPROVED*\n\n'
            'Dear {employee_name},\n'
            'Your late request for {date} has been approved.\n'
            'Late By: {late_by}\n'
            'Approved by: {approver_name}'
        ),
    },
    {
        'template_type': 'late_rejection',
        'recipient_type': 'employee',
        'template_text': (
            '❌ *Late Request REJECTED*\n\n'
            'Dear {employee_name},\n'
            'Your late request for {date} has been rejected.\n'
            'Late By: {late_by}\n'
            'Reason: {reason}\n'
            'Rejected by: {approver_name}'
        ),
    },
    {
        'template_type': 'early_request',
        'recipient_type': 'admin',
        'template_text': (
            '🏃 *Early Going Request*\n\n'
            'Employee: {employee_name}\n'
            'Date: {date}\n'
            'Early By: {early_by}\n'
            'Reason: {reason}\n\n'
            'Status: ⏳ Pending Approval'
        ),
    },
    {
        'template_type': 'early_approval',
        'recipient_type': 'employee',
        'template_text': (
            '✅ *Early Going APPROVED*\n\n'
            'Dear {employee_name},\n'
            'Your early going request for {date} has been approved.\n'
            'Early By: {early_by}\n'
            'Approved by: {approver_name}'
        ),
    },
    {
        'template_type': 'early_rejection',
        'recipient_type': 'employee',
        'template_text': (
            '❌ *Early Going REJECTED*\n\n'
            'Dear {employee_name},\n'
            'Your early going request for {date} has been rejected.\n'
            'Early By: {early_by}\n'
            'Reason: {reason}\n'
            'Rejected by: {approver_name}'
        ),
    },
    {
        'template_type': 'generic_notification',
        'recipient_type': 'both',
        'template_text': (
            '🔔 *Notification*\n\n'
            'Employee: {employee_name}\n'
            'Date: {date}\n\n'
            '{message}'
        ),
    },
]


class MessageTemplateViewSet(viewsets.ModelViewSet):
    """Manage WhatsApp message templates for each notification type."""

    queryset = MessageTemplate.objects.all().order_by('template_type')
    serializer_class = MessageTemplateSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = MessageTemplate.objects.all()
        template_type = self.request.query_params.get('type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('template_type')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'error': 'Validation failed', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"Template create error: {e}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """
        POST /api/whatsapp/admin/templates/{id}/preview/
        Preview a template with sample or custom context.
        """
        template = self.get_object()
        custom_context = request.data.get('context', {})

        default_context = {
            'employee_name': 'Arun Kumar',
            'date': '16 Mar 2026',
            'time': '09:30 AM',
            'location': 'Main Office',
            'action': 'PUNCH IN',
            'leave_type': 'Casual Leave',
            'days': '2',
            'reason': 'Personal work',
            'status': 'Approved',
            'approver_name': 'HR Manager',
            'from_date': '17 Mar 2026',
            'to_date': '18 Mar 2026',
            'late_by': '15 minutes',
            'early_by': '30 minutes',
            'message': 'Sample notification message',
        }

        full_context = {**default_context, **custom_context}

        try:
            rendered = template.render(**full_context)
            return Response({
                'success': True,
                'template_type': template.get_template_type_display(),
                'preview': rendered,
                'context_used': full_context,
            })
        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=['post'])
    def seed_defaults(self, request):
        """
        POST /api/whatsapp/admin/templates/seed_defaults/
        Create all 12 default templates (skip any that already exist).
        Safe to call multiple times.
        """
        created = []
        skipped = []

        for t in DEFAULT_TEMPLATES:
            obj, was_created = MessageTemplate.objects.get_or_create(
                template_type=t['template_type'],
                defaults={
                    'recipient_type': t['recipient_type'],
                    'template_text': t['template_text'],
                    'is_active': True,
                },
            )
            if was_created:
                created.append(t['template_type'])
                logger.info(f"Template created: {t['template_type']}")
            else:
                skipped.append(t['template_type'])

        return Response({
            'success': True,
            'created': created,
            'skipped': skipped,
            'message': f'{len(created)} template(s) created, {len(skipped)} already existed.',
        })

    @action(detail=False, methods=['post'])
    def reset_defaults(self, request):
        """
        POST /api/whatsapp/admin/templates/reset_defaults/
        Overwrite ALL templates with defaults (destructive — use seed_defaults to be safe).
        """
        updated = []
        for t in DEFAULT_TEMPLATES:
            MessageTemplate.objects.update_or_create(
                template_type=t['template_type'],
                defaults={
                    'recipient_type': t['recipient_type'],
                    'template_text': t['template_text'],
                    'is_active': True,
                },
            )
            updated.append(t['template_type'])
            logger.info(f"Template reset: {t['template_type']}")

        return Response({
            'success': True,
            'updated': updated,
            'message': f'{len(updated)} template(s) reset to defaults.',
        })


# ============================================================================
# Send Message (Admin Portal — manual send)
# ============================================================================

from rest_framework.views import APIView


class SendMessageView(APIView):
    """
    POST /api/whatsapp/admin/send/
    
    Send a WhatsApp message manually from the admin portal.

    Body options:
      1. Send to specific number:
         { "to": "+918281561081", "message": "Hello!" }

      2. Send to a named role (all active numbers with that role):
         { "role": "hr_admin", "message": "Hello!" }
         role choices: hr_admin | manager | payroll_admin | global_cc | all_admins

      3. Send to all admins + managers (no 'to' or 'role'):
         { "message": "Broadcast to all" }
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        message = (request.data.get('message') or '').strip()
        to = (request.data.get('to') or '').strip()
        role = (request.data.get('role') or '').strip()

        if not message:
            return Response(
                {'success': False, 'error': 'message is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from .utils import send_whatsapp_notification

            results = []

            # ── Case 1: explicit number ──────────────────────────────────────
            if to:
                result = send_whatsapp_notification(to, message)
                results.append({
                    'number': to,
                    'name': 'Direct',
                    'ok': result is not None,
                })

            # ── Case 2: by role ──────────────────────────────────────────────
            elif role:
                if role == 'all_admins':
                    recipients = list(
                        AdminNumber.objects.filter(is_active=True, is_api_sender=False)
                        .values('name', 'phone_number', 'role')
                    )
                else:
                    recipients = list(
                        AdminNumber.objects.filter(
                            role=role, is_active=True, is_api_sender=False
                        ).values('name', 'phone_number', 'role')
                    )

                if not recipients:
                    return Response(
                        {'success': False, 'error': f'No active numbers found for role: {role}'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                for r in recipients:
                    result = send_whatsapp_notification(r['phone_number'], message)
                    results.append({
                        'number': r['phone_number'],
                        'name': r['name'],
                        'role': r['role'],
                        'ok': result is not None,
                    })

            # ── Case 3: broadcast to all active admins ───────────────────────
            else:
                recipients = list(
                    AdminNumber.objects.filter(is_active=True, is_api_sender=False)
                    .values('name', 'phone_number', 'role')
                )

                if not recipients:
                    return Response(
                        {'success': False, 'error': 'No active admin numbers configured'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                for r in recipients:
                    result = send_whatsapp_notification(r['phone_number'], message)
                    results.append({
                        'number': r['phone_number'],
                        'name': r['name'],
                        'role': r['role'],
                        'ok': result is not None,
                    })

            success_count = sum(1 for r in results if r['ok'])
            fail_count = len(results) - success_count

            logger.info(
                f"[ADMIN SEND] Manual send: {success_count} succeeded, {fail_count} failed"
            )

            return Response({
                'success': True,
                'sent': success_count,
                'failed': fail_count,
                'results': results,
                'message': f'Message sent to {success_count} of {len(results)} recipient(s).',
            })

        except Exception as e:
            logger.exception(f"[ADMIN SEND] Error: {e}")
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )