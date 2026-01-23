# whatsapp_service/utils.py
import logging
from typing import Optional, List

from .services.whatsapp_client import send_text, WhatsAppClientError

logger = logging.getLogger(__name__)


# ================== ADMIN NUMBER HELPERS (FROM DATABASE) ==================

def get_admin_numbers_by_role(role: str, active_only: bool = True) -> List[str]:
    """
    Get admin numbers from database by role.
    Automatically excludes API sender numbers.
    """
    try:
        from .models import AdminNumber
        
        query = AdminNumber.objects.filter(role=role)
        if active_only:
            query = query.filter(is_active=True)
        
        # Exclude API sender numbers
        query = query.filter(is_api_sender=False)
        
        numbers = [admin.phone_number for admin in query]
        return numbers
    except Exception as e:
        logger.error(f"Error loading admin numbers for role {role}: {e}")
        return []


def get_hr_admin_numbers() -> List[str]:
    """Get HR admin numbers from database."""
    return get_admin_numbers_by_role('hr_admin')


def get_manager_fallback_numbers() -> List[str]:
    """Get manager numbers from database."""
    return get_admin_numbers_by_role('manager')


def get_payroll_admin_numbers() -> List[str]:
    """Get payroll admin numbers from database."""
    return get_admin_numbers_by_role('payroll_admin')


def get_global_cc_numbers() -> List[str]:
    """Get global CC numbers from database."""
    return get_admin_numbers_by_role('global_cc')


def get_all_notification_recipients() -> List[str]:
    """
    Get all unique notification recipients from database.
    Excludes API sender numbers.
    """
    try:
        from .models import AdminNumber
        
        admins = AdminNumber.objects.filter(
            is_active=True,
            is_api_sender=False  # Exclude API sender
        ).values_list('phone_number', flat=True)
        
        return list(set(admins))  # Remove duplicates
    except Exception as e:
        logger.error(f"Error loading all notification recipients: {e}")
        return []


# ================== LOW-LEVEL SEND HELPERS ==================

def send_whatsapp_notification(phone_number: str, message: str):
    """
    Send WhatsApp notification with error handling.
    Returns provider result (dict) or None on failure.
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

    qs = Employee.objects.all()
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
    """
    if not message:
        return

    numbers = get_hr_admin_numbers()
    
    if not numbers:
        logger.error("No HR admin numbers configured in database")
        return

    for num in numbers:
        send_whatsapp_notification(num, message)


# ================== MESSAGE FORMATTERS ==================

def _user_name(user) -> str:
    return getattr(user, "name", None) or getattr(user, "username", "User")


def _safe_date(dt) -> str:
    try:
        if dt:
            return dt.strftime("%d %b %Y")
    except Exception:
        pass
    return "Not specified"


def format_punch_message(user, action, location="Not recorded", time=""):
    """
    Format punch in/out message.
    action: "PUNCH IN" or "PUNCH OUT"
    """
    user_name = _user_name(user)

    return f"""📍 Attendance Alert

Employee: {user_name}
Action: {action}
Location: {location}
Time: {time}

Thank you!"""


def format_leave_request_message(leave_request):
    """Format leave request submission message (to employee + HR)."""
    user_name = _user_name(leave_request.user)

    if hasattr(leave_request, "get_leave_type_display"):
        leave_type = leave_request.get_leave_type_display()
    else:
        leave_type = getattr(leave_request, "leave_type", "Leave")

    from_date = _safe_date(getattr(leave_request, "from_date", None))
    to_date = _safe_date(getattr(leave_request, "to_date", None))
    days = getattr(leave_request, "total_days", None) or "Not specified"
    reason = getattr(leave_request, "reason", "") or "No reason provided"

    return f"""📋 Leave Request Submitted

Employee: {user_name}
Type: {leave_type}
From: {from_date}
To: {to_date}
Days: {days}
Reason: {reason}

Status: Pending Approval"""


def format_leave_approval_message(leave_request, approved_by):
    """Format leave approval/rejection message (to employee)."""
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

    status_flag = "✅ APPROVED" if getattr(leave_request, "status", "") == "approved" else "❌ REJECTED"

    return f"""📋 Leave Request {status_flag}

Employee: {user_name}
Type: {leave_type}
From: {from_date}
To: {to_date}
Days: {days}
Reason: {reason}

Status: {status_display}
Approved/Updated by: {approver_name}"""


def format_late_request_message(late_request):
    """Format late-coming request submission message."""
    user_name = _user_name(late_request.user)
    reason = getattr(late_request, "reason", "") or "No reason provided"
    late_by = getattr(late_request, "late_by_minutes", None)
    late_text = f"{late_by} minutes" if late_by is not None else "Not specified"
    date = _safe_date(getattr(late_request, "date", None))

    return f"""⏰ Late Coming Request Submitted

Employee: {user_name}
Date: {date}
Late By: {late_text}
Reason: {reason}

Status: Pending Approval"""


def format_late_approval_message(late_request, approved_by):
    """Format late-coming approval/rejection message."""
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

    status_flag = "✅ APPROVED" if getattr(late_request, "status", "") == "approved" else "❌ REJECTED"

    return f"""⏰ Late Coming Request {status_flag}

Employee: {user_name}
Date: {date}
Late By: {late_text}
Reason: {reason}

Status: {status_display}
Approved/Updated by: {approver_name}"""


def format_early_request_message(early_request):
    """Format early-going request submission message."""
    user_name = _user_name(early_request.user)
    reason = getattr(early_request, "reason", "") or "No reason provided"
    early_by = getattr(early_request, "early_by_minutes", None)
    early_text = f"{early_by} minutes" if early_by is not None else "Not specified"
    date = _safe_date(getattr(early_request, "date", None))

    return f"""⏳ Early Going Request Submitted

Employee: {user_name}
Date: {date}
Early By: {early_text}
Reason: {reason}

Status: Pending Approval"""


def format_early_approval_message(early_request, approved_by):
    """Format early-going approval/rejection message."""
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

    status_flag = "✅ APPROVED" if getattr(early_request, "status", "") == "approved" else "❌ REJECTED"

    return f"""⏳ Early Going Request {status_flag}

Employee: {user_name}
Date: {date}
Early By: {early_text}
Reason: {reason}

Status: {status_display}
Approved/Updated by: {approver_name}"""