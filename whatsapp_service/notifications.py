# FILE 5: whatsapp_service/notifications.py
# ============================================================================

import logging

from .utils import send_whatsapp_notification
from . import admin_numbers

logger = logging.getLogger(__name__)


def notify_managers_generic_request(user, text: str):
    """
    Called by /api/whatsapp/request/ when 'to' is NOT provided.

    Ignores Employee / reporting_manager completely.
    Sends the message to:
    - MANAGER_FALLBACK_NUMBERS
    - HR_ADMIN_NUMBERS

    All numbers are configured in admin_numbers.py
    """
    if not text:
        logger.warning("notify_managers_generic_request called with empty text")
        return

    # Collect recipients from config file
    recipients = set()

    for num in admin_numbers.get_manager_fallback_numbers():
        recipients.add(num)

    for num in admin_numbers.get_hr_admin_numbers():
        recipients.add(num)

    if not recipients:
        logger.error("No manager/HR numbers configured in admin_numbers.py")
        return

    logger.info("Sending generic request WhatsApp to: %s", ", ".join(recipients))

    for num in recipients:
        send_whatsapp_notification(num, text)