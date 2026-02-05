# whatsapp_service/notifications.py
"""
WhatsApp Notifications - Fully Database Driven (NO HARDCODED VALUES)

All admin numbers are loaded from the database.
NO hardcoded phone numbers.
"""

import logging

from .utils import send_whatsapp_notification, get_manager_fallback_numbers, get_hr_admin_numbers

logger = logging.getLogger(__name__)


def notify_managers_generic_request(user, text: str):
    """
    Called by /api/whatsapp/request/ when 'to' is NOT provided.

    Sends the message to:
    - Manager numbers (from database)
    - HR Admin numbers (from database)
    
    ✅ Fully database-driven - NO hardcoded numbers
    ✅ All numbers are configured in the admin panel via AdminNumber model
    
    Args:
        user: User object (for logging)
        text: Message text to send
    """
    if not text:
        logger.warning("notify_managers_generic_request called with empty text")
        return

    # Collect recipients from database
    recipients = set()

    # Get manager numbers from database
    manager_numbers = get_manager_fallback_numbers()
    for num in manager_numbers:
        recipients.add(num)

    # Get HR admin numbers from database
    hr_numbers = get_hr_admin_numbers()
    for num in hr_numbers:
        recipients.add(num)

    if not recipients:
        logger.error(
            "❌ No manager/HR numbers configured in database! "
            "Please add them in the admin panel at /api/whatsapp/admin/"
        )
        return

    logger.info(
        f"📤 Sending generic request WhatsApp to {len(recipients)} recipients: "
        f"{', '.join(recipients)}"
    )

    # Send to all recipients
    success_count = 0
    fail_count = 0
    
    for num in recipients:
        result = send_whatsapp_notification(num, text)
        if result:
            success_count += 1
        else:
            fail_count += 1
    
    logger.info(
        f"✅ Generic notification sent: {success_count} succeeded, {fail_count} failed"
    )


def notify_admins(message: str, roles: list = None):
    """
    Send notification to admins based on roles.
    
    ✅ Fully database-driven - NO hardcoded numbers
    
    Args:
        message: Message text to send
        roles: List of roles to notify (default: all active admins)
               Options: 'hr_admin', 'manager', 'payroll_admin', 'global_cc'
    """
    if not message:
        logger.warning("notify_admins called with empty message")
        return
    
    try:
        from .models import AdminNumber
        
        query = AdminNumber.objects.filter(
            is_active=True,
            is_api_sender=False
        )
        
        if roles:
            query = query.filter(role__in=roles)
        
        admin_numbers = query.values_list('phone_number', flat=True)
        recipients = list(set(admin_numbers))  # Remove duplicates
        
        if not recipients:
            logger.error(
                f"❌ No admin numbers found for roles {roles}! "
                f"Please add them in the admin panel at /api/whatsapp/admin/"
            )
            return
        
        logger.info(
            f"📤 Sending notification to {len(recipients)} admins "
            f"with roles {roles or 'all'}"
        )
        
        success_count = 0
        fail_count = 0
        
        for num in recipients:
            result = send_whatsapp_notification(num, message)
            if result:
                success_count += 1
            else:
                fail_count += 1
        
        logger.info(
            f"✅ Admin notification sent: {success_count} succeeded, {fail_count} failed"
        )
        
    except Exception as e:
        logger.error(f"Error in notify_admins: {e}")


def notify_employee(user, message: str):
    """
    Send notification to a specific employee.
    
    Args:
        user: User object
        message: Message text to send
    """
    from .utils import get_user_phone
    
    if not message:
        logger.warning("notify_employee called with empty message")
        return
    
    phone = get_user_phone(user)
    
    if not phone:
        logger.warning(
            f"⚠️  No phone number found for user {user.id}. "
            f"Cannot send WhatsApp notification."
        )
        return
    
    logger.info(f"📤 Sending notification to employee {user.id}")
    
    result = send_whatsapp_notification(phone, message)
    
    if result:
        logger.info(f"✅ Employee notification sent to {phone}")
    else:
        logger.error(f"❌ Failed to send notification to {phone}")


def notify_both_employee_and_admins(user, message: str, admin_roles: list = None):
    """
    Send notification to both employee and admins.
    
    ✅ Fully database-driven - NO hardcoded numbers
    
    Args:
        user: User object
        message: Message text to send
        admin_roles: List of admin roles to notify (default: hr_admin, manager)
    """
    if not message:
        logger.warning("notify_both_employee_and_admins called with empty message")
        return
    
    # Default roles if not specified
    if admin_roles is None:
        admin_roles = ['hr_admin', 'manager']
    
    # Send to employee
    notify_employee(user, message)
    
    # Send to admins
    notify_admins(message, roles=admin_roles)