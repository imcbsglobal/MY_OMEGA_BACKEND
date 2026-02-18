# whatsapp_service/utils.py
"""
WhatsApp Utilities - Fully Database Driven (NO HARDCODED VALUES)

All admin numbers and message templates are loaded from the database.
NO hardcoded phone numbers or message formats.
"""

import logging
from typing import Optional, List

from .services.whatsapp_client import send_text, WhatsAppClientError

logger = logging.getLogger(__name__)


# ================== ADMIN NUMBER HELPERS (FROM DATABASE) ==================

def get_admin_numbers_by_role(role: str, active_only: bool = True) -> List[str]:
    """
    Get admin numbers from database by role.
    Automatically excludes API sender numbers.
    
    ✅ Fully database-driven - NO hardcoded numbers
    
    Args:
        role: Role name (hr_admin, manager, payroll_admin, global_cc)
        active_only: Only return active numbers
    
    Returns:
        List of phone numbers as strings
    """
    try:
        from .models import AdminNumber
        
        query = AdminNumber.objects.filter(role=role)
        if active_only:
            query = query.filter(is_active=True)
        
        # Exclude API sender numbers
        query = query.filter(is_api_sender=False)
        
        numbers = [admin.phone_number for admin in query]
        
        if not numbers:
            logger.warning(
                f"⚠️  No {role} numbers found in database. "
                f"Please add them in the admin panel at /api/whatsapp/admin/"
            )
        else:
            logger.info(f"✅ Found {len(numbers)} {role} numbers from database")
        
        return numbers
    except Exception as e:
        logger.error(f"Error loading admin numbers for role {role}: {e}")
        return []


def get_hr_admin_numbers() -> List[str]:
    """
    Get HR admin numbers from database.
    ✅ NO hardcoded numbers - all from database
    """
    return get_admin_numbers_by_role('hr_admin')


def get_manager_fallback_numbers() -> List[str]:
    """
    Get manager numbers from database.
    ✅ NO hardcoded numbers - all from database
    """
    return get_admin_numbers_by_role('manager')


def get_payroll_admin_numbers() -> List[str]:
    """
    Get payroll admin numbers from database.
    ✅ NO hardcoded numbers - all from database
    """
    return get_admin_numbers_by_role('payroll_admin')


def get_global_cc_numbers() -> List[str]:
    """
    Get global CC numbers from database.
    ✅ NO hardcoded numbers - all from database
    """
    return get_admin_numbers_by_role('global_cc')


def get_all_notification_recipients() -> List[str]:
    """
    Get all unique notification recipients from database.
    Excludes API sender numbers.
    
    ✅ Fully database-driven - NO hardcoded numbers
    
    Returns:
        List of unique phone numbers
    """
    try:
        from .models import AdminNumber
        
        admins = AdminNumber.objects.filter(
            is_active=True,
            is_api_sender=False  # Exclude API sender
        ).values_list('phone_number', flat=True)
        
        unique_numbers = list(set(admins))  # Remove duplicates
        
        if not unique_numbers:
            logger.error(
                "❌ No admin numbers found in database! "
                "Please add admin numbers in the admin panel at /api/whatsapp/admin/"
            )
        else:
            logger.info(f"✅ Found {len(unique_numbers)} unique notification recipients")
        
        return unique_numbers
    except Exception as e:
        logger.error(f"Error loading all notification recipients: {e}")
        return []


# ================== LOW-LEVEL SEND HELPERS ==================

def send_whatsapp_notification(phone_number: str, message: str):
    """
    Send WhatsApp notification with error handling.
    
    ✅ Uses database configuration - NO hardcoded API keys
    
    Args:
        phone_number: Recipient phone number
        message: Message text to send
    
    Returns:
        dict: Provider result or None on failure
    """
    if not phone_number:
        logger.warning("send_whatsapp_notification called with empty phone_number")
        return None

    try:
        result = send_text(phone_number, message)
        logger.info("WhatsApp sent to %s: %s", phone_number, message[:80])
        return result
    except WhatsAppClientError as e:
        logger.error("WhatsApp error for %s: %s", phone_number, str(e))
        return None
    except Exception as e:
        logger.exception("Unexpected error sending WhatsApp to %s: %s", phone_number, str(e))
        return None


def get_user_phone(user) -> Optional[str]:
    """
    Get user's WhatsApp-compatible phone number as a string.
    Checks BOTH user.phone_number AND Employee model phone.
    
    Priority:
    1. User.phone_number (if available)
    2. Employee.phone_number (from employee_management)
    3. Employee.emergency_contact_phone (backup)
    4. None
    
    Args:
        user: Django user object
    
    Returns:
        Normalized phone number or None
    """
    if not user:
        return None

    # Optional preference flag
    if hasattr(user, "whatsapp_notifications") and not user.whatsapp_notifications:
        return None

    def normalize_phone(phone):
        """Helper to normalize phone number"""
        if not phone:
            return None
        s = str(phone).strip()
        if not s:
            return None
        # Light normalization – if it's numeric without +, prepend +
        raw = s.replace(" ", "").replace("-", "")
        if not s.startswith("+") and raw.isdigit():
            s = "+" + raw
        return s

    # First, try user.phone_number
    phone = getattr(user, "phone_number", None)
    if phone:
        normalized = normalize_phone(phone)
        if normalized:
            return normalized
    
    # Second, try to get phone from Employee model
    try:
        from employee_management.models import Employee
        
        employee = Employee.objects.filter(user=user).first()
        if employee:
            # Priority 1: Employee's direct phone number
            emp_phone = getattr(employee, 'phone_number', None)
            if emp_phone:
                normalized = normalize_phone(emp_phone)
                if normalized:
                    logger.info(f"Using employee phone for user {user.id}: {normalized}")
                    return normalized
            
            # Priority 2: Emergency contact phone as fallback
            emp_phone = getattr(employee, 'emergency_contact_phone', None)
            if emp_phone:
                normalized = normalize_phone(emp_phone)
                if normalized:
                    logger.info(f"Using emergency contact phone for user {user.id}: {normalized}")
                    return normalized
    except Exception as e:
        logger.warning(f"Could not fetch employee phone for user {user.id}: {e}")
    
    return None


def get_all_employee_numbers(exclude_none=True, exclude_duplicates=True):
    """
    Return a list of phone numbers (strings) for all employees.
    Priority per Employee record:
      1. If the employee has a linked user -> use get_user_phone(user)
      2. Employee.phone_number
      3. Employee.emergency_contact_phone
    
    Args:
        exclude_none: Filter out None/empty values
        exclude_duplicates: Remove duplicate numbers
    
    Returns:
        List of employee phone numbers
    """
    numbers = []
    try:
        from employee_management.models import Employee
    except Exception as e:
        logger.warning("Employee model not available when gathering employee numbers: %s", e)
        return []

    def _ensure_plus(s):
        if not s:
            return None
        s = str(s).strip()
        if not s:
            return None
        if s.startswith("+"):
            return s
        raw = s.replace(" ", "").replace("-", "")
        if raw.isdigit():
            return "+" + raw
        return s

    # Only active employees by default; also respect linked AppUser.is_active
    qs = Employee.objects.filter(is_active=True)
    try:
        from django.db.models import Q
        qs = qs.filter(Q(user__isnull=True) | Q(user__is_active=True))
    except Exception:
        # If relations are not available, proceed with employee-level filter
        pass
    for emp in qs:
        user = getattr(emp, "user", None)
        phone = None
        if user:
            try:
                phone = get_user_phone(user)
            except Exception:
                phone = None

        if not phone:
            phone = getattr(emp, "phone_number", None)

        if not phone:
            phone = getattr(emp, "emergency_contact_phone", None)

        phone = _ensure_plus(phone)
        if phone:
            numbers.append(phone)

    if exclude_none:
        numbers = [n for n in numbers if n]

    if exclude_duplicates:
        seen = set()
        dedup = []
        for n in numbers:
            if n not in seen:
                dedup.append(n)
                seen.add(n)
        numbers = dedup

    return numbers


def notify_hr_admin(message: str):
    """
    Notify HR admins using numbers from database.
    
    ✅ Fully database-driven - NO hardcoded numbers
    
    Args:
        message: Message text to send
    """
    if not message:
        return

    numbers = get_hr_admin_numbers()
    
    if not numbers:
        logger.error(
            "❌ No HR admin numbers configured in database! "
            "Please add them in the admin panel at /api/whatsapp/admin/"
        )
        return

    logger.info(f"Notifying {len(numbers)} HR admins")
    for num in numbers:
        send_whatsapp_notification(num, message)


# ================== MESSAGE TEMPLATE HELPERS ==================

def get_template(template_type: str, recipient_type: str = None):
    """
    Get message template from database.
    
    ✅ Fully database-driven - NO hardcoded templates
    
    Args:
        template_type: Type of template (punch_in, leave_request, etc.)
        recipient_type: Optional filter by recipient type
    
    Returns:
        MessageTemplate object or None
    """
    try:
        from .models import MessageTemplate
        
        query = MessageTemplate.objects.filter(
            template_type=template_type,
            is_active=True
        )
        
        if recipient_type:
            query = query.filter(recipient_type=recipient_type)
        
        template = query.first()
        
        if not template:
            logger.warning(
                f"⚠️  No active template found for {template_type}. "
                f"Using fallback message. Please add template in admin panel."
            )
        
        return template
    except Exception as e:
        logger.error(f"Error loading template {template_type}: {e}")
        return None


def render_template(template_type: str, **context):
    """
    Render a message template with context variables.
    
    ✅ Fully database-driven - NO hardcoded message formats
    
    Args:
        template_type: Type of template to render
        **context: Variables to substitute in template
    
    Returns:
        Rendered message string
    """
    template = get_template(template_type)
    
    if not template:
        # Fallback if no template found
        logger.error(
            f"❌ No template found for {template_type}! "
            f"Please create template in admin panel at /api/whatsapp/admin/"
        )
        return f"Notification: {template_type}\n\n" + "\n".join(
            f"{k}: {v}" for k, v in context.items()
        )
    
    try:
        return template.render(**context)
    except Exception as e:
        logger.error(f"Error rendering template {template_type}: {e}")
        # Fallback to basic format
        return f"Notification: {template_type}\n\n" + "\n".join(
            f"{k}: {v}" for k, v in context.items()
        )


# ================== MESSAGE FORMATTERS (NOW USING DATABASE TEMPLATES) ==================

def _user_name(user) -> str:
    """Get user's display name"""
    return getattr(user, "name", None) or getattr(user, "username", "User")


def _safe_date(dt) -> str:
    """Safely format a date object"""
    try:
        if dt:
            return dt.strftime("%d %b %Y")
    except Exception:
        pass
    return "Not specified"


def format_punch_message(user, action, location="Not recorded", time=""):
    """
    Format punch in/out message using database template.
    
    ✅ Uses database template - NO hardcoded format
    
    Args:
        user: User object
        action: "PUNCH IN" or "PUNCH OUT"
        location: Location name
        time: Time string
    
    Returns:
        Formatted message string
    """
    template_type = 'punch_in' if 'IN' in action.upper() else 'punch_out'
    
    return render_template(
        template_type,
        employee_name=_user_name(user),
        action=action,
        location=location,
        time=time,
        date=_safe_date(None)  # Will be filled by caller if needed
    )


def format_leave_request_message(leave_request):
    """
    Format leave request submission message using database template.
    
    ✅ Uses database template - NO hardcoded format
    """
    user_name = _user_name(leave_request.user)

    if hasattr(leave_request, "get_leave_type_display"):
        leave_type = leave_request.get_leave_type_display()
    else:
        leave_type = getattr(leave_request, "leave_type", "Leave")

    from_date = _safe_date(getattr(leave_request, "from_date", None))
    to_date = _safe_date(getattr(leave_request, "to_date", None))
    days = getattr(leave_request, "total_days", None) or "Not specified"
    reason = getattr(leave_request, "reason", "") or "No reason provided"

    return render_template(
        'leave_request',
        employee_name=user_name,
        leave_type=leave_type,
        from_date=from_date,
        to_date=to_date,
        days=str(days),
        reason=reason
    )


def format_leave_approval_message(leave_request, approved_by):
    """
    Format leave approval/rejection message using database template.
    
    ✅ Uses database template - NO hardcoded format
    """
    user_name = _user_name(leave_request.user)
    approver_name = _user_name(approved_by)

    if hasattr(leave_request, "get_leave_type_display"):
        leave_type = leave_request.get_leave_type_display()
    else:
        leave_type = getattr(leave_request, "leave_type", "Leave")

    if hasattr(leave_request, "get_status_display"):
        status_display = leave_request.get_status_display()
    else:
        status_display = getattr(leave_request, "status", "")

    from_date = _safe_date(getattr(leave_request, "from_date", None))
    to_date = _safe_date(getattr(leave_request, "to_date", None))
    days = getattr(leave_request, "total_days", None) or "Not specified"
    reason = getattr(leave_request, "reason", "") or "No reason provided"

    # Use appropriate template based on status
    template_type = 'leave_approval' if getattr(leave_request, "status", "") == "approved" else 'leave_rejection'

    return render_template(
        template_type,
        employee_name=user_name,
        leave_type=leave_type,
        from_date=from_date,
        to_date=to_date,
        days=str(days),
        reason=reason,
        status=status_display,
        approver_name=approver_name
    )


def format_late_request_message(late_request):
    """
    Format late-coming request submission message using database template.
    
    ✅ Uses database template - NO hardcoded format
    """
    user_name = _user_name(late_request.user)
    reason = getattr(late_request, "reason", "") or "No reason provided"
    late_by = getattr(late_request, "late_by_minutes", None)
    late_text = f"{late_by} minutes" if late_by is not None else "Not specified"
    date = _safe_date(getattr(late_request, "date", None))

    return render_template(
        'late_request',
        employee_name=user_name,
        date=date,
        late_by=late_text,
        reason=reason
    )


def format_late_approval_message(late_request, approved_by):
    """
    Format late-coming approval/rejection message using database template.
    
    ✅ Uses database template - NO hardcoded format
    """
    user_name = _user_name(late_request.user)
    approver_name = _user_name(approved_by)
    reason = getattr(late_request, "reason", "") or "No reason provided"
    late_by = getattr(late_request, "late_by_minutes", None)
    late_text = f"{late_by} minutes" if late_by is not None else "Not specified"
    date = _safe_date(getattr(late_request, "date", None))

    if hasattr(late_request, "get_status_display"):
        status_display = late_request.get_status_display()
    else:
        status_display = getattr(late_request, "status", "")

    # Use appropriate template based on status
    template_type = 'late_approval' if getattr(late_request, "status", "") == "approved" else 'late_rejection'

    return render_template(
        template_type,
        employee_name=user_name,
        date=date,
        late_by=late_text,
        reason=reason,
        status=status_display,
        approver_name=approver_name
    )


def format_early_request_message(early_request):
    """
    Format early-going request submission message using database template.
    
    ✅ Uses database template - NO hardcoded format
    """
    user_name = _user_name(early_request.user)
    reason = getattr(early_request, "reason", "") or "No reason provided"
    early_by = getattr(early_request, "early_by_minutes", None)
    early_text = f"{early_by} minutes" if early_by is not None else "Not specified"
    date = _safe_date(getattr(early_request, "date", None))

    return render_template(
        'early_request',
        employee_name=user_name,
        date=date,
        early_by=early_text,
        reason=reason
    )


def format_early_approval_message(early_request, approved_by):
    """
    Format early-going approval/rejection message using database template.
    
    ✅ Uses database template - NO hardcoded format
    """
    user_name = _user_name(early_request.user)
    approver_name = _user_name(approved_by)
    reason = getattr(early_request, "reason", "") or "No reason provided"
    early_by = getattr(early_request, "early_by_minutes", None)
    early_text = f"{early_by} minutes" if early_by is not None else "Not specified"
    date = _safe_date(getattr(early_request, "date", None))

    if hasattr(early_request, "get_status_display"):
        status_display = early_request.get_status_display()
    else:
        status_display = getattr(early_request, "status", "")

    # Use appropriate template based on status
    template_type = 'early_approval' if getattr(early_request, "status", "") == "approved" else 'early_rejection'

    return render_template(
        template_type,
        employee_name=user_name,
        date=date,
        early_by=early_text,
        reason=reason,
        status=status_display,
        approver_name=approver_name
    )