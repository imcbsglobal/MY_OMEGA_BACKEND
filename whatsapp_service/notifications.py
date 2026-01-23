# whatsapp_service/notifications.py
import logging

from .utils import send_whatsapp_notification, get_manager_fallback_numbers, get_hr_admin_numbers

logger = logging.getLogger(__name__)


def notify_managers_generic_request(user, text: str):
    """
    Called by /api/whatsapp/request/ when 'to' is NOT provided.

    Sends the message to:
    - Manager numbers (from database)
    - HR Admin numbers (from database)
    
    All numbers are configured in the admin panel via AdminNumber model.
    """
    if not text:
        logger.warning("notify_managers_generic_request called with empty text")
        return

    # Collect recipients from database
    recipients = set()

    # Get manager numbers from database
    for num in get_manager_fallback_numbers():
        recipients.add(num)

    # Get HR admin numbers from database
    for num in get_hr_admin_numbers():
        recipients.add(num)

    if not recipients:
        logger.error("No manager/HR numbers configured in database. Please add them in the admin panel.")
        return

    logger.info("Sending generic request WhatsApp to: %s", ", ".join(recipients))

    for num in recipients:
        send_whatsapp_notification(num, text)