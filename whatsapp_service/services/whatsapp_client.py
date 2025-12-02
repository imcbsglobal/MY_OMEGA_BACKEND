# whatsapp_service/services/whatsapp_client.py

import logging
import urllib.parse
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
        # DXING: expects numeric MSISDN in `recipient` param (digits only).
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
    Send a text WhatsApp message via DXING, using query params like:

    https://app.dxing.in/api/send/whatsapp
      ?secret=...
      &account=...
      &recipient=$NO$
      &type=text
      &message=$MSG$
      &priority=1
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

    params = {
        "secret": secret,
        "account": account,
        "recipient": to,
        "type": "text",
        "message": message,
        "priority": getattr(settings, "DXING_DEFAULT_PRIORITY", 1),
    }

    url = f"{api_url}?{urllib.parse.urlencode(params)}"
    # don't log raw secret
    logger.debug(
        "DXING request URL (masked): %s",
        url.replace(secret, "[SECRET]") if secret else url,
    )

    try:
        resp = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        logger.exception("DXING request failed: %s", exc)
        raise WhatsAppClientError(f"DXING request failed: {exc}") from exc

    # parse response
    content_type = resp.headers.get("Content-Type", "")
    try:
        if "application/json" in content_type:
            data = resp.json()
        else:
            data = {"status_code": resp.status_code, "text": resp.text}
    except Exception:
        data = {"status_code": resp.status_code, "text": resp.text}

    if not resp.ok:
        logger.error("DXING returned HTTP %s: %s", resp.status_code, data)
        raise WhatsAppClientError(
            f"DXING returned HTTP {resp.status_code}: {data}"
        )

    logger.info("DXING send succeeded: HTTP %s, recipient=%s", resp.status_code, to)
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
