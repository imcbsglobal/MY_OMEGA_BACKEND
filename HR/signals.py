# HR/signals.py - COMPLETE FIX: Fully Database-Driven (NO hardcoded numbers)
"""
✅ FIXED VERSION - Use this to replace your HR/signals.py

Changes from original:
1. Removed: from whatsapp_service import admin_numbers
2. Removed: notify_hr_admin import (doesn't exist)
3. Added: get_hr_admin_numbers, get_manager_fallback_numbers (database-driven)
4. Updated: send_to_managers_and_hr to use database functions
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
import logging

from .models import Attendance, LeaveRequest, LateRequest, EarlyRequest

logger = logging.getLogger(__name__)

# ============================================================================
# Import WhatsApp utilities - FIXED: Database-driven functions ONLY
# ============================================================================
try:
    from whatsapp_service.utils import (
        send_whatsapp_notification,
        get_user_phone,
        get_hr_admin_numbers,          # ✅ Database-driven (added)
        get_manager_fallback_numbers,  # ✅ Database-driven (added)
        format_punch_message,
        format_leave_request_message,
        format_leave_approval_message,
        format_late_request_message,
        format_late_approval_message,
        format_early_request_message,
        format_early_approval_message,
    )
    # ❌ REMOVED: from whatsapp_service import admin_numbers
    # ❌ REMOVED: notify_hr_admin import
    WHATSAPP_ENABLED = True
    print("✅ WhatsApp service loaded successfully (DATABASE-DRIVEN)")
except Exception as e:
    WHATSAPP_ENABLED = False
    print(f"❌ WhatsApp service not available - notifications disabled: {e}")


# ============================================================================
# HELPER FUNCTION - FIXED: Database-driven
# ============================================================================

def send_to_managers_and_hr(message):
    """
    Send message to all managers and HR admins from DATABASE.
    
    ✅ Fully database-driven - NO hardcoded numbers
    ✅ Loads numbers from AdminNumber model via utils.py
    ✅ Respects is_active and is_api_sender flags
    """
    if not WHATSAPP_ENABLED:
        print("⚠️  WhatsApp not enabled - skipping notification")
        return
    
    recipients = set()
    
    # Add manager numbers from DATABASE
    try:
        manager_numbers = get_manager_fallback_numbers()
        for num in manager_numbers:
            recipients.add(num)
        if manager_numbers:
            print(f"✅ Loaded {len(manager_numbers)} manager numbers from database")
    except Exception as e:
        print(f"❌ Error getting manager numbers from database: {e}")
        import traceback
        traceback.print_exc()
    
    # Add HR admin numbers from DATABASE
    try:
        hr_numbers = get_hr_admin_numbers()
        for num in hr_numbers:
            recipients.add(num)
        if hr_numbers:
            print(f"✅ Loaded {len(hr_numbers)} HR admin numbers from database")
    except Exception as e:
        print(f"❌ Error getting HR numbers from database: {e}")
        import traceback
        traceback.print_exc()
    
    if not recipients:
        print("⚠️  No recipients found! Please add admin numbers in the admin panel at /api/whatsapp/admin/")
        return
    
    print(f"📤 Sending to {len(recipients)} recipients: {', '.join(recipients)}")
    
    # Send to all recipients
    success_count = 0
    fail_count = 0
    for phone in recipients:
        try:
            result = send_whatsapp_notification(phone, message)
            if result:
                success_count += 1
                print(f"✅ Sent to {phone}")
            else:
                fail_count += 1
                print(f"❌ Failed to send to {phone}")
        except Exception as e:
            fail_count += 1
            print(f"❌ Failed to send WhatsApp to {phone}: {e}")
    
    print(f"📊 Notification results: {success_count} succeeded, {fail_count} failed")


# ============================================================================
# LEAVE REQUEST SIGNALS
# ============================================================================

@receiver(post_save, sender=LeaveRequest)
def handle_leave_request_notifications(sender, instance, created, **kwargs):
    """Handle WhatsApp notifications for leave requests"""
    transaction.on_commit(lambda: _send_leave_notifications(instance, created, kwargs))


def _send_leave_notifications(instance, created, kwargs):
    """Actually send the notifications (called after transaction)"""
    if not WHATSAPP_ENABLED:
        return

    try:
        if getattr(instance, '_signal_processing', False):
            return
        instance._signal_processing = True

        if created:
            print(f"[HR/signals] New leave request created for user {instance.user.id}")
            try:
                message = format_leave_request_message(instance)
                send_to_managers_and_hr(message)
                print(f"[HR/signals] Leave request notification sent")
            except Exception as e:
                print(f"[HR/signals] Failed to send leave request notification: {e}")
        
        else:
            update_fields = kwargs.get('update_fields')
            status_changed = (
                update_fields is None or 
                (update_fields and 'status' in update_fields)
            )
            
            if status_changed and instance.status in ['approved', 'rejected']:
                print(f"[HR/signals] Leave request {instance.status}")
                try:
                    user_phone = get_user_phone(instance.user)
                    if user_phone:
                        approved_by = instance.reviewed_by or instance.user
                        message = format_leave_approval_message(instance, approved_by)
                        send_whatsapp_notification(user_phone, message)
                        print(f"[HR/signals] Leave {instance.status} notification sent")
                except Exception as e:
                    print(f"[HR/signals] Failed to send leave approval notification: {e}")

    except Exception as e:
        print(f"[HR/signals] Error in leave notifications: {e}")
    finally:
        if hasattr(instance, '_signal_processing'):
            delattr(instance, '_signal_processing')


# ============================================================================
# LATE REQUEST SIGNALS
# ============================================================================

@receiver(post_save, sender=LateRequest)
def handle_late_request_notifications(sender, instance, created, **kwargs):
    """Handle WhatsApp notifications for late requests"""
    transaction.on_commit(lambda: _send_late_notifications(instance, created, kwargs))


def _send_late_notifications(instance, created, kwargs):
    """Actually send the notifications (called after transaction)"""
    if not WHATSAPP_ENABLED:
        return

    try:
        if getattr(instance, '_signal_processing', False):
            return
        instance._signal_processing = True

        if created:
            print(f"[HR/signals] New late request created for user {instance.user.id}")
            try:
                if not instance.user:
                    print("[HR/signals] No user attached to late request")
                    return
                
                message = format_late_request_message(instance)
                send_to_managers_and_hr(message)
                print(f"[HR/signals] Late request notification sent")
                
            except Exception as e:
                print(f"[HR/signals] Failed to send late request notification: {e}")
                import traceback
                traceback.print_exc()
        
        else:
            update_fields = kwargs.get('update_fields')
            status_changed = (
                update_fields is None or 
                (update_fields and 'status' in update_fields)
            )
            
            if status_changed and instance.status in ['approved', 'rejected']:
                print(f"[HR/signals] Late request {instance.status}")
                try:
                    user_phone = get_user_phone(instance.user)
                    if user_phone:
                        approved_by = instance.reviewed_by or instance.user
                        message = format_late_approval_message(instance, approved_by)
                        send_whatsapp_notification(user_phone, message)
                        print(f"[HR/signals] Late {instance.status} notification sent")
                except Exception as e:
                    print(f"[HR/signals] Failed to send late approval notification: {e}")

    except Exception as e:
        print(f"[HR/signals] Error in late notifications: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if hasattr(instance, '_signal_processing'):
            delattr(instance, '_signal_processing')


# ============================================================================
# EARLY REQUEST SIGNALS
# ============================================================================

@receiver(post_save, sender=EarlyRequest)
def handle_early_request_notifications(sender, instance, created, **kwargs):
    """Handle WhatsApp notifications for early requests"""
    transaction.on_commit(lambda: _send_early_notifications(instance, created, kwargs))


def _send_early_notifications(instance, created, kwargs):
    """Actually send the notifications (called after transaction)"""
    if not WHATSAPP_ENABLED:
        return

    try:
        if getattr(instance, '_signal_processing', False):
            return
        instance._signal_processing = True

        if created:
            print(f"[HR/signals] New early request created for user {instance.user.id}")
            try:
                if not instance.user:
                    print("[HR/signals] No user attached to early request")
                    return
                
                message = format_early_request_message(instance)
                send_to_managers_and_hr(message)
                print(f"[HR/signals] Early request notification sent")
                
            except Exception as e:
                print(f"[HR/signals] Failed to send early request notification: {e}")
                import traceback
                traceback.print_exc()
        
        else:
            update_fields = kwargs.get('update_fields')
            status_changed = (
                update_fields is None or 
                (update_fields and 'status' in update_fields)
            )
            
            if status_changed and instance.status in ['approved', 'rejected']:
                print(f"[HR/signals] Early request {instance.status}")
                try:
                    user_phone = get_user_phone(instance.user)
                    if user_phone:
                        approved_by = instance.reviewed_by or instance.user
                        message = format_early_approval_message(instance, approved_by)
                        send_whatsapp_notification(user_phone, message)
                        print(f"[HR/signals] Early {instance.status} notification sent")
                except Exception as e:
                    print(f"[HR/signals] Failed to send early approval notification: {e}")

    except Exception as e:
        print(f"[HR/signals] Error in early notifications: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if hasattr(instance, '_signal_processing'):
            delattr(instance, '_signal_processing')


# ============================================================================
# STORE OLD VALUES BEFORE SAVE
# ============================================================================

@receiver(pre_save, sender=Attendance)
def store_old_attendance_values(sender, instance, **kwargs):
    """Store old values before save for comparison"""
    if instance.pk:  # Only for existing records (updates)
        try:
            old_instance = Attendance.objects.get(pk=instance.pk)
            instance._old_first_punch_in = old_instance.first_punch_in_time
            instance._old_last_punch_out = old_instance.last_punch_out_time
            print(f"[pre_save] Stored old values - first_punch_in: {instance._old_first_punch_in}, last_punch_out: {instance._old_last_punch_out}")
        except Attendance.DoesNotExist:
            instance._old_first_punch_in = None
            instance._old_last_punch_out = None
            print(f"[pre_save] Could not find old instance")
    else:  # New record (creation)
        instance._old_first_punch_in = None
        instance._old_last_punch_out = None
        print(f"[pre_save] New attendance record - no old values")


# ============================================================================
# ATTENDANCE PUNCH IN/OUT SIGNALS
# ============================================================================

@receiver(post_save, sender=Attendance)
def handle_punch_notifications(sender, instance, created, **kwargs):
    """Handle WhatsApp notifications for punch in/out"""
    print(f"\n{'='*60}")
    print(f"[post_save] Attendance signal triggered")
    print(f"[post_save] Created: {created}")
    print(f"[post_save] User: {instance.user.id}")
    print(f"[post_save] First Punch IN: {instance.first_punch_in_time}")
    print(f"[post_save] Last Punch OUT: {instance.last_punch_out_time}")
    print(f"{'='*60}\n")
    
    transaction.on_commit(lambda: _send_punch_notifications(instance, created))


def _send_punch_notifications(instance, created):
    """Actually send the notifications (called after transaction)"""
    print(f"\n[_send_punch_notifications] Starting...")
    
    if not WHATSAPP_ENABLED:
        print(f"[_send_punch_notifications] ❌ WhatsApp not enabled - skipping")
        return

    try:
        if getattr(instance, '_signal_processing', False):
            print(f"[_send_punch_notifications] ⚠️  Already processing - skipping")
            return
        instance._signal_processing = True

        user_phone = get_user_phone(instance.user)
        print(f"[_send_punch_notifications] User phone: {user_phone}")
        
        if not user_phone:
            print(f"[_send_punch_notifications] ❌ No phone number for user {instance.user.id}")
            return

        # ===== PUNCH IN NOTIFICATION =====
        if created and instance.first_punch_in_time:
            print(f"\n[PUNCH IN] Detected punch in event")
            print(f"[PUNCH IN] User: {instance.user.id}")
            print(f"[PUNCH IN] Time: {instance.first_punch_in_time}")
            print(f"[PUNCH IN] Location: {instance.first_punch_in_location}")
            
            try:
                msg = format_punch_message(
                    user=instance.user,
                    action="PUNCH IN",
                    location=instance.first_punch_in_location or "Not recorded",
                    time=instance.first_punch_in_time.strftime("%I:%M %p"),
                )
                print(f"[PUNCH IN] Message formatted: {msg[:100]}...")
                
                result = send_whatsapp_notification(user_phone, msg)
                
                print(f"[PUNCH IN] ✅ Notification sent successfully to {user_phone}")
                print(f"[PUNCH IN] Result: {result}")
            except Exception as e:
                print(f"[PUNCH IN] ❌ Error sending notification: {e}")
                import traceback
                traceback.print_exc()

        # ===== PUNCH OUT NOTIFICATION =====
        if not created:
            old_punch_out = getattr(instance, '_old_last_punch_out', None)
            new_punch_out = instance.last_punch_out_time
            
            print(f"\n[PUNCH OUT] Checking for punch out event")
            print(f"[PUNCH OUT] Old last_punch_out: {old_punch_out}")
            print(f"[PUNCH OUT] New last_punch_out: {new_punch_out}")
            print(f"[PUNCH OUT] User: {instance.user.id} ({instance.user.name if hasattr(instance.user, 'name') else 'N/A'})")
            print(f"[PUNCH OUT] Phone: {user_phone}")
            
            is_punch_out = (old_punch_out is None) and (new_punch_out is not None)
            print(f"[PUNCH OUT] Is punch out event? {is_punch_out}")
            
            if is_punch_out:
                print(f"[PUNCH OUT] ✅ Punch out event detected!")
                print(f"[PUNCH OUT] Location: {instance.last_punch_out_location}")
                print(f"[PUNCH OUT] Working hours: {instance.total_working_hours}")
                
                try:
                    msg = format_punch_message(
                        user=instance.user,
                        action="PUNCH OUT",
                        location=instance.last_punch_out_location or "Not recorded",
                        time=new_punch_out.strftime("%I:%M %p"),
                    )
                    print(f"[PUNCH OUT] Message formatted:")
                    print(f"[PUNCH OUT] {msg}")
                    print(f"[PUNCH OUT] Sending to: {user_phone}")
                    
                    result = send_whatsapp_notification(user_phone, msg)
                    
                    print(f"[PUNCH OUT] ✅ Notification sent successfully!")
                    print(f"[PUNCH OUT] Result: {result}")
                    
                except Exception as e:
                    print(f"[PUNCH OUT] ❌ Error sending notification: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[PUNCH OUT] ℹ️  Not a punch out event")

    except Exception as e:
        print(f"[_send_punch_notifications] ❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if hasattr(instance, '_signal_processing'):
            delattr(instance, '_signal_processing')
        print(f"[_send_punch_notifications] Finished\n")