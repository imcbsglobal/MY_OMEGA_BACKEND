# whatsapp_service/admin_numbers.py
"""
Central place to manage admin WhatsApp numbers.

IMPORTANT: All numbers MUST be in FULL INTERNATIONAL FORMAT
Examples:
  ✅ CORRECT: "+918281561081"
  ❌ WRONG:   "8281561081" (missing country code)
  ❌ WRONG:   "918281561081" (missing + sign)
"""

# ========== HR / ATTENDANCE ADMINS ==========
# People who receive HR-related and attendance-related notifications
HR_ADMIN_NUMBERS = [
    "+917356122119",     # HR Admin
    # Add more HR admin numbers here
]

# Optional: a single "main HR" number (used as ultimate fallback)
HR_MAIN_NUMBER = "+918281561081"


# ========== MANAGER FALLBACK ==========
# Used when an employee has NO reporting_manager set in Employee model
# These managers will receive ALL leave/late/early requests
MANAGER_FALLBACK_NUMBERS = [
    "+918129139506",     # Manager #1
    "+918281561081",     # Manager #2 (also HR)
    # Add more manager numbers here
]


# ========== PAYROLL ADMINS (Optional) ==========
# People who should see payroll / salary issue messages
PAYROLL_ADMIN_NUMBERS = [
    # Add payroll numbers here if needed
]


# ========== GLOBAL CC (Optional) ==========
# People who should be CC'd on important messages
GLOBAL_CC_NUMBERS = [
    # Example:
    # "+919876543210",
]


# ========== HELPERS (DON'T EDIT BELOW THIS LINE) ==========

def _normalize(numbers):
    """Normalize and validate phone numbers"""
    cleaned = []
    for n in numbers or []:
        if not n:
            continue
        s = str(n).strip()
        if not s:
            continue
        if not s.startswith("+"):
            # If caller forgot +, we add it
            s = "+" + s
        if s not in cleaned:
            cleaned.append(s)
    return cleaned


def get_hr_admin_numbers():
    """Get list of HR admin phone numbers"""
    return _normalize(HR_ADMIN_NUMBERS)


def get_hr_main_number():
    """Get the main HR phone number"""
    if HR_MAIN_NUMBER:
        normalized = _normalize([HR_MAIN_NUMBER])
        return normalized[0] if normalized else None
    hr = get_hr_admin_numbers()
    return hr[0] if hr else None


def get_payroll_admin_numbers():
    """Get list of payroll admin phone numbers"""
    return _normalize(PAYROLL_ADMIN_NUMBERS)


def get_manager_fallback_numbers():
    """Get list of fallback manager phone numbers"""
    return _normalize(MANAGER_FALLBACK_NUMBERS)


def get_global_cc_numbers():
    """Get list of global CC phone numbers"""
    return _normalize(GLOBAL_CC_NUMBERS)


def get_all_notification_recipients():
    """Get all unique notification recipients (HR + Managers)"""
    all_numbers = set()
    all_numbers.update(get_hr_admin_numbers())
    all_numbers.update(get_manager_fallback_numbers())
    return list(all_numbers)


# Debug helper
def print_config():
    """Print current configuration (for debugging)"""
    print("=" * 60)
    print("WhatsApp Admin Numbers Configuration")
    print("=" * 60)
    print(f"HR Admins: {get_hr_admin_numbers()}")
    print(f"Managers: {get_manager_fallback_numbers()}")
    print(f"Payroll: {get_payroll_admin_numbers()}")
    print(f"Global CC: {get_global_cc_numbers()}")
    print(f"All Recipients: {get_all_notification_recipients()}")
    print("=" * 60)