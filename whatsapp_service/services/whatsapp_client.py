
# ============================================================================
# FILE 1: whatsapp_service/services/whatsapp_client.py
# ============================================================================

import logging
import json
from typing import Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppClientError(Exception):
    """Raised when the WhatsApp provider rejects or cannot send a message."""
    pass


def _normalize_number_for_provider(n: Optional[str], provider: str) -> str:
    """
    Normalize a phone/WhatsApp recipient according to provider expectations.

    For DXING we send a numeric MSISDN with country code, e.g.:
      "8281561081"      -> "918281561081"
      "+918281561081"   -> "918281561081"
      "00918281561081"  -> "918281561081"
    """

    if not n:
        raise WhatsAppClientError("Recipient number is empty")

    s = str(n).strip()
    if not s:
        raise WhatsAppClientError("Recipient number is empty")

    provider = (provider or "").lower()

    if provider == "meta":
        # Meta Cloud API expects plain digits, no '+'
        if s.startswith("+"):
            s = s[1:]
        if s.startswith("00"):
            s = s[2:]
        digits = "".join(ch for ch in s if ch.isdigit())
        if not digits:
            raise WhatsAppClientError(f"Invalid Meta phone number: {n!r}")
        return digits

    elif provider == "twilio":
        # Twilio expects "whatsapp:+<country><number>"
        digits = "".join(ch for ch in s if ch.isdigit())
        if not digits:
            raise WhatsAppClientError(f"Invalid Twilio phone number: {n!r}")
        # assume digits already include country code, just add '+'
        s = "+" + digits.lstrip("0").lstrip("+")
        if not s.startswith("whatsapp:"):
            s = "whatsapp:" + s
        return s

    elif provider in ("dxing", "external_dx", "external"):
        # DXING: expects numeric MSISDN (digits only).
        # 1) strip '+' / '00'
        if s.startswith("+"):
            s = s[1:]
        if s.startswith("00"):
            s = s[2:]
        # 2) keep only digits
        digits = "".join(ch for ch in s if ch.isdigit())
        if not digits:
            raise WhatsAppClientError(f"Invalid DXING phone number: {n!r}")
        # 3) If 10-digit Indian mobile (6-9), prepend '91'
        if len(digits) == 10 and digits[0] in "6789":
            digits = "91" + digits
        return digits

    else:
        # default: return stripped as-is
        return s


def _send_via_dxing(recipient: str, message: str, priority: int = 1, timeout: int = 15):
    """
    Send a text WhatsApp message via DXING using POST with JSON body.
    
    CORRECT API FORMAT (POST with JSON):
    POST https://app.dxing.in/api/send/whatsapp
    Content-Type: application/json
    
    {
        "secret": "your_api_secret",
        "account": "your_account_id",
        "recipient": "919895123456",
        "type": "text",
        "message": "Hello! This is a test message.",
        "priority": 1
    }
    
    Response:
    {
        "status": 200,
        "message": "Your message was successfully delivered",
        "data": {
            "messageId": "DXWA_544614"
        }
    }
    """
    api_url = getattr(settings, "DXING_API_URL",
                      "https://app.dxing.in/api/send/whatsapp").rstrip("/")
    secret = getattr(settings, "DXING_SECRET", None)
    account = getattr(settings, "DXING_ACCOUNT", None)

    if not secret or not account:
        raise WhatsAppClientError(
            "DXING credentials not configured (DXING_SECRET / DXING_ACCOUNT)"
        )

    to = _normalize_number_for_provider(recipient, "dxing")

    # Prepare JSON payload
    payload = {
        "secret": secret,
        "account": account,
        "recipient": to,
        "type": "text",
        "message": message,
        "priority": priority,
    }

    headers = {
        "Content-Type": "application/json"
    }

    logger.debug(
        "DXING request: POST %s with recipient=%s, message length=%d",
        api_url, to, len(message)
    )

    try:
        # IMPORTANT: Use POST with JSON body, not GET with query params
        resp = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=timeout
        )
    except requests.RequestException as exc:
        logger.exception("DXING request failed: %s", exc)
        raise WhatsAppClientError(f"DXING request failed: {exc}") from exc

    # Parse response
    try:
        data = resp.json()
    except Exception as e:
        logger.error("Failed to parse DXING response as JSON: %s", resp.text)
        data = {"status_code": resp.status_code, "text": resp.text}

    # Log the full response for debugging
    logger.info(
        "DXING response: status_code=%s, body=%s",
        resp.status_code, json.dumps(data, indent=2)
    )

    # Check for success
    # DXING returns status: 200 in the JSON body for success
    if isinstance(data, dict):
        response_status = data.get("status", resp.status_code)
        response_message = data.get("message", "")
        
        # Success conditions:
        # 1. HTTP 200 AND JSON status: 200
        # 2. JSON message contains success indicators
        if response_status == 200 or "success" in response_message.lower() or "delivered" in response_message.lower():
            logger.info(
                "DXING send succeeded: recipient=%s, messageId=%s",
                to, data.get("data", {}).get("messageId", "N/A")
            )
            return data
        else:
            # Error in response
            error_msg = data.get("message", data.get("text", "Unknown error"))
            logger.error("DXING returned error: %s", error_msg)
            raise WhatsAppClientError(f"DXING error: {error_msg}")
    
    # If response is not a dict or doesn't have expected structure
    if not resp.ok:
        logger.error("DXING returned HTTP %s: %s", resp.status_code, data)
        raise WhatsAppClientError(
            f"DXING returned HTTP {resp.status_code}: {data}"
        )

    return data


def send_text(recipient: str, message: str, priority: int = 1, timeout: int = 15):
    """
    High-level send function used by the rest of the app.
    Chooses provider based on settings.WHATSAPP_PROVIDER.
    """
    provider = getattr(settings, "WHATSAPP_PROVIDER", "dxing").lower()

    if provider == "dxing":
        return _send_via_dxing(recipient, message, priority=priority, timeout=timeout)

    # If later you want to support meta/twilio, add branches here.
    raise WhatsAppClientError(f"Unsupported WhatsApp provider: {provider}")
