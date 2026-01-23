# whatsapp_service/services/whatsapp_client.py
import logging
import json
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class WhatsAppClientError(Exception):
    """Raised when the WhatsApp provider rejects or cannot send a message."""
    pass


def _get_active_config():
    """
    Get the active WhatsApp configuration from database.
    Returns dict with provider, api_url, api_secret, account_id, default_priority
    """
    try:
        from whatsapp_service.models import WhatsAppConfiguration
        config = WhatsAppConfiguration.objects.filter(is_active=True).first()
        
        if not config:
            logger.error("No active WhatsApp configuration found in database")
            raise WhatsAppClientError(
                "No active WhatsApp configuration. Please configure one in the admin panel."
            )
        
        return {
            'provider': config.provider,
            'api_url': config.api_url,
            'api_secret': config.api_secret,
            'account_id': config.account_id,
            'default_priority': config.default_priority,
        }
    except Exception as e:
        logger.exception(f"Error loading WhatsApp configuration: {e}")
        raise WhatsAppClientError(f"Failed to load WhatsApp configuration: {e}")


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


def _send_via_dxing(recipient: str, message: str, priority: int = 1, timeout: int = 15, config: dict = None):
    """
    Send a text WhatsApp message via DXING using POST with JSON body.
    """
    if config is None:
        config = _get_active_config()
    
    api_url = config['api_url'].rstrip("/")
    secret = config['api_secret']
    account = config['account_id']

    if not secret or not account:
        raise WhatsAppClientError(
            "DXING credentials not configured. Please configure in admin panel."
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
    if isinstance(data, dict):
        response_status = data.get("status", resp.status_code)
        response_message = data.get("message", "")
        
        if response_status == 200 or "success" in response_message.lower() or "delivered" in response_message.lower():
            logger.info(
                "DXING send succeeded: recipient=%s, messageId=%s",
                to, data.get("data", {}).get("messageId", "N/A")
            )
            return data
        else:
            error_msg = data.get("message", data.get("text", "Unknown error"))
            logger.error("DXING returned error: %s", error_msg)
            raise WhatsAppClientError(f"DXING error: {error_msg}")
    
    if not resp.ok:
        logger.error("DXING returned HTTP %s: %s", resp.status_code, data)
        raise WhatsAppClientError(
            f"DXING returned HTTP {resp.status_code}: {data}"
        )

    return data


def send_text(recipient: str, message: str, priority: int = None, timeout: int = 15):
    """
    High-level send function used by the rest of the app.
    Reads configuration from database instead of settings.py
    """
    # Get active configuration from database
    config = _get_active_config()
    
    # Use config priority if not specified
    if priority is None:
        priority = config['default_priority']
    
    provider = config['provider'].lower()

    if provider == "dxing":
        return _send_via_dxing(recipient, message, priority=priority, timeout=timeout, config=config)

    # If later you want to support meta/twilio, add branches here.
    raise WhatsAppClientError(f"Unsupported WhatsApp provider: {provider}")