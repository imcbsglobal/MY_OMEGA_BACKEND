# whatsapp_service/admin_numbers.py
"""
Central place to manage admin WhatsApp numbers.

IMPORTANT: All numbers MUST be in FULL INTERNATIONAL FORMAT
Example:
  "+919089786756"
"""

# ========== YOUR API NUMBER (DON'T SEND TO THIS) ==========
# This is the number that SENDS messages via DXING
# We should NEVER send notifications TO this number
# This number will be AUTOMATICALLY EXCLUDED from all recipient lists
API_SENDER_NUMBER = None  # Set this if your API has a fixed sender number


# ========== HR / ATTENDANCE ADMINS ==========
# Add your HR team numbers here
HR_ADMIN_NUMBERS = [
    "+917356122119",     # HR Admin 1 - REPLACE WITH REAL NUMBER
    #  "+918281561081",     # HR Admin 2 - REPLACE WITH REAL NUMBER
]

# Main HR fallback
HR_MAIN_NUMBER = "++917356122119",   # REPLACE WITH REAL NUMBER


# ========== MANAGER FALLBACK ==========
# These managers receive ALL:
# - Leave requests
# - Late/Early requests
# - Generic WhatsApp messages (when "to" not provided)
MANAGER_FALLBACK_NUMBERS = [
    # "+917356122119", 
    "+918281561081",     # Manager (the number you mentioned)
    # Add more manager numbers if needed
]


# ========== PAYROLL ADMINS (Optional) ==========
PAYROLL_ADMIN_NUMBERS = [
    # Add payroll numbers here if needed
]


# ========== GLOBAL CC (Optional) ==========
GLOBAL_CC_NUMBERS = [
    # Optional CC numbers
]


# ========== HELPERS (DON'T EDIT BELOW THIS LINE) ==========

def _normalize(numbers, exclude_api=True):
    """
    Normalize and deduplicate numbers.
    If exclude_api=True, removes the API_SENDER_NUMBER from the list.
    """
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
        
        # Skip if this is the API sender number
        if exclude_api and api_normalized and s == api_normalized:
            continue
            
        if s not in cleaned:
            cleaned.append(s)
    
    return cleaned


def get_hr_admin_numbers():
    """Get HR admin numbers, excluding the API sender number."""
    return _normalize(HR_ADMIN_NUMBERS, exclude_api=True)


def get_hr_main_number():
    """Get main HR number, excluding the API sender number."""
    if HR_MAIN_NUMBER:
        normalized = _normalize([HR_MAIN_NUMBER], exclude_api=True)
        return normalized[0] if normalized else None
    hr = get_hr_admin_numbers()
    return hr[0] if hr else None


def get_payroll_admin_numbers():
    """Get payroll admin numbers, excluding the API sender number."""
    return _normalize(PAYROLL_ADMIN_NUMBERS, exclude_api=True)


def get_manager_fallback_numbers():
    """Get manager fallback numbers, excluding the API sender number."""
    return _normalize(MANAGER_FALLBACK_NUMBERS, exclude_api=True)


def get_global_cc_numbers():
    """Get global CC numbers, excluding the API sender number."""
    return _normalize(GLOBAL_CC_NUMBERS, exclude_api=True)


def get_all_notification_recipients():
    """Get all unique notification recipients, excluding the API sender number."""
    all_numbers = set()
    all_numbers.update(get_hr_admin_numbers())
    all_numbers.update(get_manager_fallback_numbers())
    return list(all_numbers)


def print_config():
    """Print the current configuration."""
    print("=" * 60)
    print("WhatsApp Admin Numbers Configuration")
    print("=" * 60)
    print(f"API Sender (EXCLUDED): {API_SENDER_NUMBER or 'Not set'}")
    print(f"HR Admins: {get_hr_admin_numbers()}")
    print(f"Managers: {get_manager_fallback_numbers()}")
    print(f"Payroll: {get_payroll_admin_numbers()}")
    print(f"Global CC: {get_global_cc_numbers()}")
    print(f"All Recipients: {get_all_notification_recipients()}")
    print("=" * 60)