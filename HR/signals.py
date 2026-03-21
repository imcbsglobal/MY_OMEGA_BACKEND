# HR/signals.py
"""
HR Signals — WhatsApp Notifications (Database-Driven)

Punch in/out  → notify EMPLOYEE + HR/Managers
Leave/Late/Early requests → notify HR/Managers
Leave/Late/Early approvals → notify EMPLOYEE
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
import logging

from .models import Attendance, LeaveRequest, LateRequest, EarlyRequest

logger = logging.getLogger(__name__)

# ============================================================================
# Load WhatsApp utilities
# ============================================================================
try:
    from whatsapp_service.utils import (
        send_whatsapp_notification,
        send_to_managers_and_hr,      # ✅ sends to all HR + managers from DB
        get_user_phone,
        get_hr_admin_numbers,
        get_manager_fallback_numbers,
        format_punch_message,
        format_leave_request_message,
        format_leave_approval_message,
        format_late_request_message,
        format_late_approval_message,
        format_early_request_message,
        format_early_approval_message,
    )
    WHATSAPP_ENABLED = True
    logger.info("✅ WhatsApp service loaded (DATABASE-DRIVEN)")
except Exception as e:
    WHATSAPP_ENABLED = False
    logger.error(f"❌ WhatsApp service not available — notifications disabled: {e}")


# ============================================================================
# ATTENDANCE — store old values before update
# ============================================================================

@receiver(pre_save, sender=Attendance)
def store_old_attendance_values(sender, instance, **kwargs):
    """Snapshot old punch times so we can detect actual changes in post_save."""
    if instance.pk:
        try:
            old = Attendance.objects.get(pk=instance.pk)
            instance._old_first_punch_in  = old.first_punch_in_time
            instance._old_last_punch_out  = old.last_punch_out_time
        except Attendance.DoesNotExist:
            instance._old_first_punch_in  = None
            instance._old_last_punch_out  = None
    else:
        instance._old_first_punch_in  = None
        instance._old_last_punch_out  = None


# ============================================================================
# ATTENDANCE — punch in / punch out notifications
# ============================================================================

@receiver(post_save, sender=Attendance)
def handle_punch_notifications(sender, instance, created, **kwargs):
    transaction.on_commit(lambda: _send_punch_notifications(instance, created))


def _send_punch_notifications(instance, created):
    if not WHATSAPP_ENABLED:
        logger.warning("[PUNCH] WhatsApp not enabled — skipping")
        return

    if getattr(instance, '_signal_processing', False):
        return
    instance._signal_processing = True

    try:
        from django.utils import timezone as tz

        user_phone = get_user_phone(instance.user)

        # ── PUNCH IN ────────────────────────────────────────────────────────
        if created and instance.first_punch_in_time:
            logger.info(f"[PUNCH IN] User {instance.user.id} at {instance.first_punch_in_time}")

            local_time = tz.localtime(instance.first_punch_in_time)
            msg = format_punch_message(
                user=instance.user,
                action="PUNCH IN",
                location=instance.first_punch_in_location or "Not recorded",
                time=local_time.strftime("%I:%M %p"),
                date=local_time.strftime("%d %b %Y"),
            )

            # 1. Notify employee
            if user_phone:
                result = send_whatsapp_notification(user_phone, msg)
                logger.info(f"[PUNCH IN] Employee notified → {user_phone}: {result}")
            else:
                logger.warning(f"[PUNCH IN] No phone for user {instance.user.id}")

            # 2. Notify HR / Managers
            send_to_managers_and_hr(msg)
            logger.info("[PUNCH IN] HR/Manager notification sent")

        # ── PUNCH OUT ───────────────────────────────────────────────────────
        if not created:
            old_punch_out = getattr(instance, '_old_last_punch_out', None)
            new_punch_out = instance.last_punch_out_time

            # Only fire when last_punch_out changes from None → a value
            if old_punch_out is None and new_punch_out is not None:
                logger.info(f"[PUNCH OUT] User {instance.user.id} at {new_punch_out}")

                local_time = tz.localtime(new_punch_out)
                msg = format_punch_message(
                    user=instance.user,
                    action="PUNCH OUT",
                    location=instance.last_punch_out_location or "Not recorded",
                    time=local_time.strftime("%I:%M %p"),
                    date=local_time.strftime("%d %b %Y"),
                )

                # 1. Notify employee
                if user_phone:
                    result = send_whatsapp_notification(user_phone, msg)
                    logger.info(f"[PUNCH OUT] Employee notified → {user_phone}: {result}")
                else:
                    logger.warning(f"[PUNCH OUT] No phone for user {instance.user.id}")

                # 2. Notify HR / Managers
                send_to_managers_and_hr(msg)
                logger.info("[PUNCH OUT] HR/Manager notification sent")

    except Exception as e:
        logger.exception(f"[PUNCH] Unexpected error: {e}")
    finally:
        if hasattr(instance, '_signal_processing'):
            delattr(instance, '_signal_processing')


# ============================================================================
# LEAVE REQUEST SIGNALS
# ============================================================================

@receiver(post_save, sender=LeaveRequest)
def handle_leave_request_notifications(sender, instance, created, **kwargs):
    transaction.on_commit(lambda: _send_leave_notifications(instance, created, kwargs))


def _send_leave_notifications(instance, created, kwargs):
    if not WHATSAPP_ENABLED:
        return

    if getattr(instance, '_signal_processing', False):
        return
    instance._signal_processing = True

    try:
        if created:
            # New request — alert managers/HR
            message = format_leave_request_message(instance)
            send_to_managers_and_hr(message)
            logger.info(f"[LEAVE] New request notification sent for user {instance.user.id}")
        else:
            update_fields = kwargs.get('update_fields')
            status_changed = (
                update_fields is None or
                (update_fields and 'status' in update_fields)
            )
            if status_changed and instance.status in ['approved', 'rejected']:
                user_phone = get_user_phone(instance.user)
                if user_phone:
                    approved_by = getattr(instance, 'reviewed_by', None) or instance.user
                    message = format_leave_approval_message(instance, approved_by)
                    send_whatsapp_notification(user_phone, message)
                    logger.info(f"[LEAVE] {instance.status.title()} notification sent to {user_phone}")
    except Exception as e:
        logger.exception(f"[LEAVE] Error: {e}")
    finally:
        if hasattr(instance, '_signal_processing'):
            delattr(instance, '_signal_processing')


# ============================================================================
# LATE REQUEST SIGNALS
# ============================================================================

@receiver(post_save, sender=LateRequest)
def handle_late_request_notifications(sender, instance, created, **kwargs):
    transaction.on_commit(lambda: _send_late_notifications(instance, created, kwargs))


def _send_late_notifications(instance, created, kwargs):
    if not WHATSAPP_ENABLED:
        return

    if getattr(instance, '_signal_processing', False):
        return
    instance._signal_processing = True

    try:
        if created:
            message = format_late_request_message(instance)
            send_to_managers_and_hr(message)
            logger.info(f"[LATE] New request notification sent for user {instance.user.id}")
        else:
            update_fields = kwargs.get('update_fields')
            status_changed = (
                update_fields is None or
                (update_fields and 'status' in update_fields)
            )
            if status_changed and instance.status in ['approved', 'rejected']:
                user_phone = get_user_phone(instance.user)
                if user_phone:
                    approved_by = getattr(instance, 'reviewed_by', None) or instance.user
                    message = format_late_approval_message(instance, approved_by)
                    send_whatsapp_notification(user_phone, message)
                    logger.info(f"[LATE] {instance.status.title()} notification sent to {user_phone}")
    except Exception as e:
        logger.exception(f"[LATE] Error: {e}")
    finally:
        if hasattr(instance, '_signal_processing'):
            delattr(instance, '_signal_processing')


# ============================================================================
# EARLY REQUEST SIGNALS
# ============================================================================

@receiver(post_save, sender=EarlyRequest)
def handle_early_request_notifications(sender, instance, created, **kwargs):
    transaction.on_commit(lambda: _send_early_notifications(instance, created, kwargs))


def _send_early_notifications(instance, created, kwargs):
    if not WHATSAPP_ENABLED:
        return

    if getattr(instance, '_signal_processing', False):
        return
    instance._signal_processing = True

    try:
        if created:
            message = format_early_request_message(instance)
            send_to_managers_and_hr(message)
            logger.info(f"[EARLY] New request notification sent for user {instance.user.id}")
        else:
            update_fields = kwargs.get('update_fields')
            status_changed = (
                update_fields is None or
                (update_fields and 'status' in update_fields)
            )
            if status_changed and instance.status in ['approved', 'rejected']:
                user_phone = get_user_phone(instance.user)
                if user_phone:
                    approved_by = getattr(instance, 'reviewed_by', None) or instance.user
                    message = format_early_approval_message(instance, approved_by)
                    send_whatsapp_notification(user_phone, message)
                    logger.info(f"[EARLY] {instance.status.title()} notification sent to {user_phone}")
    except Exception as e:
        logger.exception(f"[EARLY] Error: {e}")
    finally:
        if hasattr(instance, '_signal_processing'):
            delattr(instance, '_signal_processing')