# ============================================================================
# FILE 4: whatsapp_service/views.py
# ============================================================================

from datetime import datetime
from django.utils import timezone
import pytz
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import SendMessageSerializer
from django.conf import settings
from .utils import (
    send_whatsapp_notification,
    get_user_phone,
    get_all_employee_numbers,
    format_punch_message,
)
from .notifications import notify_managers_generic_request
import logging

logger = logging.getLogger(__name__)


def get_ist_time():
    """
    Get current time in IST (India Standard Time)
    Always returns the correct IST time regardless of server timezone
    """
    # Define IST timezone
    ist = pytz.timezone('Asia/Kolkata')
    
    # Get current UTC time and convert to IST
    utc_now = timezone.now()
    ist_now = utc_now.astimezone(ist)
    
    # Log for debugging
    logger.info(f"[TIME DEBUG] UTC: {utc_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"[TIME DEBUG] IST: {ist_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    return ist_now


class PunchInView(APIView):
    """
    POST /api/whatsapp/punchin/

    Body:
    {
      "to": "+91...",   # optional; if missing, uses request.user.phone_number
      "location": "..." # optional; location string
    }
    
    NOTE: Time is ALWAYS generated server-side. Do not send 'message' or 'time' in request.
    """

    def post(self, request):
        # IMPORTANT: Always generate time on server side in IST
        current_time = get_ist_time()
        formatted_time = current_time.strftime("%I:%M %p")  # Format: 11:26 AM
        formatted_date = current_time.strftime("%d %b %Y")  # Format: 18 Dec 2024
        
        # Log the actual time being used
        logger.info(f"[PUNCH IN] IST Time: {formatted_time} on {formatted_date}")
        
        # Get location from request data if provided
        location = request.data.get("location", "Not recorded")
        
        # Get user
        user = getattr(request, "user", None)

        # ALWAYS create the message on server side with server time
        message = format_punch_message(
            user=user,
            action="PUNCH IN",
            location=location,
            time=f"{formatted_time} on {formatted_date}"
        )
        
        # Log the final message for verification
        logger.info(f"[PUNCH IN] Message: {message[:100]}...")

        # Get recipient
        to = (request.data.get("to") or "").strip() or None
        if not to and user is not None:
            to = get_user_phone(user)

        if not to:
            return Response(
                {"ok": False, "error": "Recipient phone number not available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Send the message
        result = send_whatsapp_notification(to, message)
        if result is None:
            return Response(
                {"ok": False, "error": "Failed to send WhatsApp message."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Broadcast to all employees if the feature flag is enabled
        if getattr(settings, "WHATSAPP_NOTIFY_ALL_EMPLOYEES_ON_PUNCH", False):
            try:
                employee_numbers = get_all_employee_numbers()
                logger.info("Broadcasting punch-in to all employees: count=%s", len(employee_numbers))
                for num in employee_numbers:
                    if num == to:
                        continue
                    try:
                        send_whatsapp_notification(num, message)
                    except Exception as e:
                        logger.exception("Failed to send punch-in to %s: %s", num, e)
            except Exception as e:
                logger.exception("Failed while broadcasting punch-in to all employees: %s", e)

        return Response({
            "ok": True, 
            "result": result, 
            "time_ist": formatted_time,
            "date_ist": formatted_date
        })


class PunchOutView(APIView):
    """
    POST /api/whatsapp/punchout/

    Body:
    {
      "to": "+91...",   # optional; if missing, uses request.user.phone_number
      "location": "..." # optional; location string
    }
    
    NOTE: Time is ALWAYS generated server-side. Do not send 'message' or 'time' in request.
    """

    def post(self, request):
        # IMPORTANT: Always generate time on server side in IST
        current_time = get_ist_time()
        formatted_time = current_time.strftime("%I:%M %p")  # Format: 11:26 AM
        formatted_date = current_time.strftime("%d %b %Y")  # Format: 18 Dec 2024
        
        # Log the actual time being used
        logger.info(f"[PUNCH OUT] IST Time: {formatted_time} on {formatted_date}")
        
        # Get location from request data if provided
        location = request.data.get("location", "Not recorded")
        
        # Get user
        user = getattr(request, "user", None)

        # ALWAYS create the message on server side with server time
        message = format_punch_message(
            user=user,
            action="PUNCH OUT",
            location=location,
            time=f"{formatted_time} on {formatted_date}"
        )
        
        # Log the final message for verification
        logger.info(f"[PUNCH OUT] Message: {message[:100]}...")

        # Get recipient
        to = (request.data.get("to") or "").strip() or None
        if not to and user is not None:
            to = get_user_phone(user)

        if not to:
            return Response(
                {"ok": False, "error": "Recipient phone number not available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Send the message
        result = send_whatsapp_notification(to, message)
        if result is None:
            return Response(
                {"ok": False, "error": "Failed to send WhatsApp message."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Broadcast to all employees if the feature flag is enabled
        if getattr(settings, "WHATSAPP_NOTIFY_ALL_EMPLOYEES_ON_PUNCH", False):
            try:
                employee_numbers = get_all_employee_numbers()
                logger.info("Broadcasting punch-out to all employees: count=%s", len(employee_numbers))
                for num in employee_numbers:
                    if num == to:
                        continue
                    try:
                        send_whatsapp_notification(num, message)
                    except Exception as e:
                        logger.exception("Failed to send punch-out to %s: %s", num, e)
            except Exception as e:
                logger.exception("Failed while broadcasting punch-out to all employees: %s", e)

        return Response({
            "ok": True, 
            "result": result, 
            "time_ist": formatted_time,
            "date_ist": formatted_date
        })


class GenericRequestView(APIView):
    """
    POST /api/whatsapp/request/

    Body:
    {
      "to": "+91...",   # optional; if present, send directly
      "message": "..."  # required
    }

    Behaviour:
    - If 'to' is provided -> send directly to that number.
    - If 'to' is missing/blank -> send to the manager/HR numbers defined
      in whatsapp_service/admin_numbers.py
    """

    def post(self, request):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]
        to = (serializer.validated_data.get("to") or "").strip() or None

        # Case 1: explicit recipient
        if to:
            result = send_whatsapp_notification(to, message)
            if result is None:
                return Response(
                    {"ok": False, "error": "Failed to send WhatsApp message."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )
            return Response({"ok": True, "mode": "direct", "result": result})

        # Case 2: no 'to' -> route to configured manager/HR numbers
        notify_managers_generic_request(request.user, message)
        return Response({"ok": True, "mode": "managers_routed"})