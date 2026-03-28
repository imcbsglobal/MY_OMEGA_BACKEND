# whatsapp_service/admin_numbers.py
"""
Central place to manage admin WhatsApp numbers.

⚠️  This file is a LEGACY fallback only.
    The system is now fully DATABASE-DRIVEN.
    All admin numbers should be managed via the admin panel at /api/whatsapp/admin/

    This file's helpers (get_hr_admin_numbers, etc.) now pull from the DB,
    NOT from the hardcoded lists below. The lists below are intentionally empty.
"""

# ========== YOUR API NUMBER (DON'T SEND TO THIS) ==========
API_SENDER_NUMBER = None  # Set this if your API has a fixed sender number

# ========== LEAVE EMPTY — USE ADMIN PANEL INSTEAD ==========
# All numbers are now managed in the database via /api/whatsapp/admin/admin-numbers/
HR_ADMIN_NUMBERS = []
HR_MAIN_NUMBER = None
MANAGER_FALLBACK_NUMBERS = []
PAYROLL_ADMIN_NUMBERS = []
GLOBAL_CC_NUMBERS = []


# ========== HELPERS (DATABASE-DRIVEN) ==========

def _normalize(numbers, exclude_api=True):
    cleaned = []
    api_normalized = None
    if exclude_api and API_SENDER_NUMBER:
        api_normalized = str(API_SENDER_NUMBER).strip()
        if not api_normalized.startswith("+"):
            api_normalized = "+" + api_normalized
    for n in numbers or []:
        if not n:
            continue
        s = str(n).strip()
        if not s:
            continue
        if not s.startswith("+"):
            s = "+" + s
        if exclude_api and api_normalized and s == api_normalized:
            continue
        if s not in cleaned:
            cleaned.append(s)
    return cleaned


def get_hr_admin_numbers():
    """Get HR admin numbers from DATABASE (not hardcoded list)."""
    try:
        from whatsapp_service.models import AdminNumber
        numbers = list(
            AdminNumber.objects.filter(
                role='hr_admin', is_active=True, is_api_sender=False
            ).values_list('phone_number', flat=True)
        )
        return numbers
    except Exception:
        return _normalize(HR_ADMIN_NUMBERS)


def get_hr_main_number():
    hr = get_hr_admin_numbers()
    return hr[0] if hr else None


def get_payroll_admin_numbers():
    try:
        from whatsapp_service.models import AdminNumber
        return list(
            AdminNumber.objects.filter(
                role='payroll_admin', is_active=True, is_api_sender=False
            ).values_list('phone_number', flat=True)
        )
    except Exception:
        return _normalize(PAYROLL_ADMIN_NUMBERS)


def get_manager_fallback_numbers():
    """Get manager numbers from DATABASE (not hardcoded list)."""
    try:
        from whatsapp_service.models import AdminNumber
        numbers = list(
            AdminNumber.objects.filter(
                role='manager', is_active=True, is_api_sender=False
            ).values_list('phone_number', flat=True)
        )
        return numbers
    except Exception:
        return _normalize(MANAGER_FALLBACK_NUMBERS)


def get_global_cc_numbers():
    try:
        from whatsapp_service.models import AdminNumber
        return list(
            AdminNumber.objects.filter(
                role='global_cc', is_active=True, is_api_sender=False
            ).values_list('phone_number', flat=True)
        )
    except Exception:
        return _normalize(GLOBAL_CC_NUMBERS)


def get_all_notification_recipients():
    """Get all unique notification recipients from database."""
    try:
        from whatsapp_service.models import AdminNumber
        numbers = list(
            AdminNumber.objects.filter(
                is_active=True, is_api_sender=False
            ).values_list('phone_number', flat=True)
        )
        return list(set(numbers))
    except Exception:
        all_numbers = set()
        all_numbers.update(get_hr_admin_numbers())
        all_numbers.update(get_manager_fallback_numbers())
        return list(all_numbers)


def print_config():
    print("=" * 60)
    print("WhatsApp Admin Numbers Configuration (DATABASE-DRIVEN)")
    print("=" * 60)
    print(f"API Sender (EXCLUDED): {API_SENDER_NUMBER or 'Not set'}")
    print(f"HR Admins: {get_hr_admin_numbers()}")
    print(f"Managers: {get_manager_fallback_numbers()}")
    print(f"Payroll: {get_payroll_admin_numbers()}")
    print(f"Global CC: {get_global_cc_numbers()}")
    print(f"All Recipients: {get_all_notification_recipients()}")
    print("=" * 60)