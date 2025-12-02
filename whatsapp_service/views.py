# whatsapp_service/views.py

from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import SendMessageSerializer
from .utils import send_whatsapp_notification, get_user_phone
from .notifications import notify_managers_generic_request


class PunchInView(APIView):
    """
    POST /api/whatsapp/punchin/

    Body:
    {
      "to": "+91...",   # optional; if missing, uses request.user.phone_number
      "message": "..."  # optional; default "Punch IN at <timestamp>"
    }
    """

    def post(self, request):
        data = request.data.copy()

        if "message" not in data or not data.get("message"):
            data["message"] = f"Punch IN at {datetime.utcnow().isoformat()}"

        serializer = SendMessageSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]
        to = (serializer.validated_data.get("to") or "").strip() or None

        if not to and getattr(request, "user", None) is not None:
            to = get_user_phone(request.user)

        if not to:
            return Response(
                {"ok": False, "error": "Recipient phone number not available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = send_whatsapp_notification(to, message)
        if result is None:
            return Response(
                {"ok": False, "error": "Failed to send WhatsApp message."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"ok": True, "result": result})


class PunchOutView(APIView):
    """
    POST /api/whatsapp/punchout/

    Same behaviour as PunchInView, but default message is "Punch OUT ...".
    """

    def post(self, request):
        data = request.data.copy()

        if "message" not in data or not data.get("message"):
            data["message"] = f"Punch OUT at {datetime.utcnow().isoformat()}"

        serializer = SendMessageSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]
        to = (serializer.validated_data.get("to") or "").strip() or None

        if not to and getattr(request, "user", None) is not None:
            to = get_user_phone(request.user)

        if not to:
            return Response(
                {"ok": False, "error": "Recipient phone number not available."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = send_whatsapp_notification(to, message)
        if result is None:
            return Response(
                {"ok": False, "error": "Failed to send WhatsApp message."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"ok": True, "result": result})


# whatsapp_service/views.py (only GenericRequestView part)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import SendMessageSerializer
from .utils import send_whatsapp_notification, get_user_phone
from .notifications import notify_managers_generic_request


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

