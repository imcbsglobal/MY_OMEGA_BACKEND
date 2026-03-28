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
        get_template,                 # ✅ read recipient_type from DB template
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

# In-process dedup set: tracks (attendance_pk, event) pairs already queued
# for on_commit in the current request cycle. Prevents double-queueing when
# the same Attendance row is saved more than once in a single request.
_punch_notified = set()


@receiver(pre_save, sender=Attendance)
def store_old_attendance_values(sender, instance, **kwargs):
    """Snapshot old punch times so we can detect actual changes in post_save."""
    if instance.pk:
        try:
            old_obj = Attendance.objects.get(pk=instance.pk)
            instance._old_first_punch_in = old_obj.first_punch_in_time
            instance._old_last_punch_out = old_obj.last_punch_out_time
        except Attendance.DoesNotExist:
            instance._old_first_punch_in = None
            instance._old_last_punch_out = None
    else:
        instance._old_first_punch_in = None
        instance._old_last_punch_out = None


# ============================================================================
# ATTENDANCE — punch in / punch out notifications
# ============================================================================

@receiver(post_save, sender=Attendance)
def handle_punch_notifications(sender, instance, created, **kwargs):
    """
    Queue punch notifications to run after the DB transaction commits.

    Dedup logic (two layers):
      1. _punch_notified set  — prevents the same event being queued twice
         in the same Python process request (e.g. two saves in one request).
      2. Inside _send_punch_notifications — re-reads the DB to confirm the
         punch time actually exists before sending, so stale on_commit
         closures are harmless.
    """
    pk = instance.pk

    # ── PUNCH IN dedup ──────────────────────────────────────────────────────
    if created and instance.first_punch_in_time:
        key = (pk, 'punch_in')
        if key not in _punch_notified:
            _punch_notified.add(key)
            # Capture values NOW (closure over primitives, not the ORM instance)
            user_id       = instance.user_id
            punch_in_time = instance.first_punch_in_time
            location      = instance.first_punch_in_location or "Not recorded"
            transaction.on_commit(
                lambda uid=user_id, t=punch_in_time, loc=location, k=key:
                    _send_punch_in(uid, t, loc, k)
            )

    # ── PUNCH OUT dedup ─────────────────────────────────────────────────────
    if not created:
        old_punch_out = getattr(instance, '_old_last_punch_out', None)
        new_punch_out = instance.last_punch_out_time
        if old_punch_out is None and new_punch_out is not None:
            key = (pk, 'punch_out')
            if key not in _punch_notified:
                _punch_notified.add(key)
                user_id        = instance.user_id
                punch_out_time = instance.last_punch_out_time
                location       = instance.last_punch_out_location or "Not recorded"
                transaction.on_commit(
                    lambda uid=user_id, t=punch_out_time, loc=location, k=key:
                        _send_punch_out(uid, t, loc, k)
                )


def _send_punch_in(user_id, punch_time, location, dedup_key):
    """Send PUNCH IN notification. Runs after DB commit."""
    # Remove from dedup set so future punches on a new request work normally
    _punch_notified.discard(dedup_key)

    if not WHATSAPP_ENABLED:
        return

    try:
        from django.contrib.auth import get_user_model
        from django.utils import timezone as tz

        User = get_user_model()
        user = User.objects.get(pk=user_id)

        local_time = tz.localtime(punch_time)
        msg = format_punch_message(
            user=user,
            action="PUNCH IN",
            location=location,
            time=local_time.strftime("%I:%M %p"),
            date=local_time.strftime("%d %b %Y"),
        )

        punch_in_template = get_template('punch_in')
        recipient_type = getattr(punch_in_template, 'recipient_type', 'both')
        logger.info(f"[PUNCH IN] template recipient_type='{recipient_type}' for user {user_id}")

        # Notify employee
        if recipient_type in ('employee', 'both'):
            phone = get_user_phone(user)
            if phone:
                result = send_whatsapp_notification(phone, msg)
                logger.info(f"[PUNCH IN] Employee notified → {phone}: {result}")
            else:
                logger.warning(f"[PUNCH IN] No phone for user {user_id}")

        # Notify HR / Managers
        if recipient_type in ('admin', 'both'):
            send_to_managers_and_hr(msg)
            logger.info("[PUNCH IN] HR/Manager notification sent")
        else:
            logger.info(f"[PUNCH IN] Skipping HR/Manager (recipient_type='{recipient_type}')")

    except Exception as e:
        logger.exception(f"[PUNCH IN] Error for user {user_id}: {e}")


def _send_punch_out(user_id, punch_time, location, dedup_key):
    """Send PUNCH OUT notification. Runs after DB commit."""
    _punch_notified.discard(dedup_key)

    if not WHATSAPP_ENABLED:
        return

    try:
        from django.contrib.auth import get_user_model
        from django.utils import timezone as tz

        User = get_user_model()
        user = User.objects.get(pk=user_id)

        local_time = tz.localtime(punch_time)
        msg = format_punch_message(
            user=user,
            action="PUNCH OUT",
            location=location,
            time=local_time.strftime("%I:%M %p"),
            date=local_time.strftime("%d %b %Y"),
        )

        punch_out_template = get_template('punch_out')
        recipient_type = getattr(punch_out_template, 'recipient_type', 'both')
        logger.info(f"[PUNCH OUT] template recipient_type='{recipient_type}' for user {user_id}")

        # Notify employee
        if recipient_type in ('employee', 'both'):
            phone = get_user_phone(user)
            if phone:
                result = send_whatsapp_notification(phone, msg)
                logger.info(f"[PUNCH OUT] Employee notified → {phone}: {result}")
            else:
                logger.warning(f"[PUNCH OUT] No phone for user {user_id}")

        # Notify HR / Managers
        if recipient_type in ('admin', 'both'):
            send_to_managers_and_hr(msg)
            logger.info("[PUNCH OUT] HR/Manager notification sent")
        else:
            logger.info(f"[PUNCH OUT] Skipping HR/Manager (recipient_type='{recipient_type}')")

    except Exception as e:
        logger.exception(f"[PUNCH OUT] Error for user {user_id}: {e}")


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