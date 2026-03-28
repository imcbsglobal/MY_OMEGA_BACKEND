# whatsapp_service/views.py
"""
WhatsApp Service Views

PunchInView  / PunchOutView  — send notification to EMPLOYEE ONLY
                               (no admin/HR notifications for punch events)
GenericRequestView             — send to explicit 'to' or fall back to managers
"""

from django.utils import timezone
import pytz
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from .serializers import SendMessageSerializer
from .utils import (
    send_whatsapp_notification,
    send_to_managers_and_hr,
    get_user_phone,
    get_all_employee_numbers,
    format_punch_message,
)
from .notifications import notify_managers_generic_request
import logging

logger = logging.getLogger(__name__)


def get_ist_time():
    """Return current time as an IST-aware datetime object."""
    ist = pytz.timezone('Asia/Kolkata')
    return timezone.now().astimezone(ist)


class PunchInView(APIView):
    """
    POST /api/whatsapp/punchin/

    Body (all optional):
      { "to": "+91...", "location": "..." }

    - Sends punch-in message to the EMPLOYEE ONLY.
    - Does NOT send to HR/admins (punch events are employee-only notifications).
    - The template's recipient_type is respected:
        'employee' or 'both' → message is sent
        'admin'              → skipped (admin-only templates not sent to employees)
    """

    def post(self, request):
        current_time = get_ist_time()
        formatted_time = current_time.strftime("%I:%M %p")
        formatted_date = current_time.strftime("%d %b %Y")
        logger.info(f"[PUNCH IN] IST: {formatted_time} on {formatted_date}")

        location = request.data.get("location", "Not recorded")
        user = getattr(request, "user", None)

        # ── Check if the punch_in template is meant for employees ──
        from .utils import get_template
        template = get_template('punch_in')
        if template and template.recipient_type == 'admin':
            # Template is admin-only; skip employee send
            logger.info("[PUNCH IN] punch_in template is admin-only, skipping employee send")
            return Response({"ok": True, "mode": "skipped_admin_only_template"})

        message = format_punch_message(
            user=user,
            action="PUNCH IN",
            location=location,
            time=formatted_time,
            date=formatted_date,
        )

        # Determine employee recipient
        to = (request.data.get("to") or "").strip() or None
        if not to and user is not None:
            to = get_user_phone(user)

        if not to:
            return Response(
                {"ok": False, "error": "Recipient phone number not available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Send to EMPLOYEE ONLY ──
        result = send_whatsapp_notification(to, message)
        if result is None:
            return Response(
                {"ok": False, "error": "Failed to send WhatsApp message to employee."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # ── NO send_to_managers_and_hr() here ──
        # Punch events go to the employee only.
        # If you want admin alerts for punch events, create a separate
        # endpoint or add it explicitly with a clear intent.

        # Optional broadcast to all employees (disabled by default)
        if getattr(settings, "WHATSAPP_NOTIFY_ALL_EMPLOYEES_ON_PUNCH", False):
            try:
                for num in get_all_employee_numbers():
                    if num != to:
                        try:
                            send_whatsapp_notification(num, message)
                        except Exception as e:
                            logger.exception("Broadcast punch-in failed for %s: %s", num, e)
            except Exception as e:
                logger.exception("Broadcast punch-in error: %s", e)

        return Response({
            "ok": True,
            "result": result,
            "time_ist": formatted_time,
            "date_ist": formatted_date,
        })


class PunchOutView(APIView):
    """
    POST /api/whatsapp/punchout/

    Body (all optional):
      { "to": "+91...", "location": "..." }

    - Sends punch-out message to the EMPLOYEE ONLY.
    - Does NOT send to HR/admins (punch events are employee-only notifications).
    """

    def post(self, request):
        current_time = get_ist_time()
        formatted_time = current_time.strftime("%I:%M %p")
        formatted_date = current_time.strftime("%d %b %Y")
        logger.info(f"[PUNCH OUT] IST: {formatted_time} on {formatted_date}")

        location = request.data.get("location", "Not recorded")
        user = getattr(request, "user", None)

        # ── Check if the punch_out template is meant for employees ──
        from .utils import get_template
        template = get_template('punch_out')
        if template and template.recipient_type == 'admin':
            logger.info("[PUNCH OUT] punch_out template is admin-only, skipping employee send")
            return Response({"ok": True, "mode": "skipped_admin_only_template"})

        message = format_punch_message(
            user=user,
            action="PUNCH OUT",
            location=location,
            time=formatted_time,
            date=formatted_date,
        )

        # Determine employee recipient
        to = (request.data.get("to") or "").strip() or None
        if not to and user is not None:
            to = get_user_phone(user)

        if not to:
            return Response(
                {"ok": False, "error": "Recipient phone number not available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Send to EMPLOYEE ONLY ──
        result = send_whatsapp_notification(to, message)
        if result is None:
            return Response(
                {"ok": False, "error": "Failed to send WhatsApp message to employee."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # ── NO send_to_managers_and_hr() here ──

        # Optional broadcast to all employees (disabled by default)
        if getattr(settings, "WHATSAPP_NOTIFY_ALL_EMPLOYEES_ON_PUNCH", False):
            try:
                for num in get_all_employee_numbers():
                    if num != to:
                        try:
                            send_whatsapp_notification(num, message)
                        except Exception as e:
                            logger.exception("Broadcast punch-out failed for %s: %s", num, e)
            except Exception as e:
                logger.exception("Broadcast punch-out error: %s", e)

        return Response({
            "ok": True,
            "result": result,
            "time_ist": formatted_time,
            "date_ist": formatted_date,
        })


class GenericRequestView(APIView):
    """
    POST /api/whatsapp/request/

    Body:
      { "to": "+91...", "message": "..." }

    - If 'to' is provided → send directly to that number.
    - If 'to' is missing  → route to all configured managers/HR.
    """

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]
        to = (serializer.validated_data.get("to") or "").strip() or None

        if to:
            result = send_whatsapp_notification(to, message)
            if result is None:
                return Response(
                    {"ok": False, "error": "Failed to send WhatsApp message."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            return Response({"ok": True, "mode": "direct", "result": result})

        # No explicit recipient — route to managers/HR
        notify_managers_generic_request(request.user, message)
        return Response({"ok": True, "mode": "managers_routed"})