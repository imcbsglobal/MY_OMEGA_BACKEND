# This endpoint handles daily penalty waive/deduct actions
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from datetime import datetime
from employee_management.models import Employee
from User.models import AppUser
from .models import LateRequest, EarlyRequest, Attendance, PunchRecord
import logging

logger = logging.getLogger('django')


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def apply_daily_penalty_action(request):
    """
    Apply waive/deduct action to a specific day's penalties for an employee.
    
    Request body:
    {
        "employee_id": 1,
        "date": "2025-05-15",  # YYYY-MM-DD
        "action": "waive" or "deduct",  # What to do with this day's penalties
        "penalty_type": "late", "early", or "missed"  # Which type of penalty
    }
    """
    
    try:
        employee_id = request.data.get('employee_id')
        date_str = request.data.get('date')
        action = request.data.get('action', '').lower()
        penalty_type = request.data.get('penalty_type', '').lower()
        
        if not employee_id or not date_str or action not in ['waive', 'deduct'] or penalty_type not in ['late', 'early', 'missed']:
            return Response({
                'error': 'Missing or invalid parameters: employee_id, date (YYYY-MM-DD), action (waive/deduct), penalty_type (late/early/missed)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        employee = Employee.objects.get(id=employee_id)
        user = employee.user
        
        if not user:
            return Response({'error': 'Employee has no linked user account'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Parse date
        try:
            penalty_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Map action to status: 'waive' -> 'rejected', 'deduct' -> 'approved'
        new_status = 'approved' if action == 'deduct' else 'rejected'
        
        updated_count = 0
        message = ''
        
        with transaction.atomic():
            if penalty_type == 'late':
                # Don't change LateRequest status - that's for Leave Management approval
                # Only record the waive/deduct decision in Attendance for payroll
                attendance = Attendance.objects.filter(user=user, date=penalty_date).first()
                
                if attendance:
                    # Record waive/deduct in admin_note for payroll tracking
                    if action == 'waive':
                        admin_note = f'Late penalty waived on {timezone.now().strftime("%Y-%m-%d")}'
                    else:  # deduct
                        admin_note = f'Late penalty deducted on {timezone.now().strftime("%Y-%m-%d")}'
                    
                    # Add to existing admin_note
                    if attendance.admin_note:
                        attendance.admin_note += f"\n{admin_note}"
                    else:
                        attendance.admin_note = admin_note
                    attendance.save()
                    updated_count = 1
                    message = f'Successfully {action}d late penalty for {date_str}'
                else:
                    message = f'No attendance record found for {date_str}'
                    updated_count = 0
            
            elif penalty_type == 'early':
                # Don't change EarlyRequest status - that's for Leave Management approval
                # Only record the waive/deduct decision in Attendance for payroll
                attendance = Attendance.objects.filter(user=user, date=penalty_date).first()
                
                if attendance:
                    # Record waive/deduct in admin_note for payroll tracking
                    if action == 'waive':
                        admin_note = f'Early exit penalty waived on {timezone.now().strftime("%Y-%m-%d")}'
                    else:  # deduct
                        admin_note = f'Early exit penalty deducted on {timezone.now().strftime("%Y-%m-%d")}'
                    
                    # Add to existing admin_note
                    if attendance.admin_note:
                        attendance.admin_note += f"\n{admin_note}"
                    else:
                        attendance.admin_note = admin_note
                    attendance.save()
                    updated_count = 1
                    message = f'Successfully {action}d early exit penalty for {date_str}'
                else:
                    message = f'No attendance record found for {date_str}'
                    updated_count = 0
            
            elif penalty_type == 'missed':
                # For missed punches, update the attendance record's penalty waiver flag
                attendance = Attendance.objects.filter(
                    user=user,
                    date=penalty_date
                ).first()

                duty_start = getattr(employee, 'duty_time_start', None) or getattr(user, 'duty_time_start', None)
                duty_end = getattr(employee, 'duty_time_end', None) or getattr(user, 'duty_time_end', None)

                def _make_admin_dt(clock_time):
                    if not clock_time:
                        return None
                    return timezone.make_aware(
                        datetime.combine(penalty_date, clock_time),
                        timezone.get_current_timezone()
                    )

                def _stamp_admin_note(att, text):
                    stamped = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {text}"
                    if att.admin_note:
                        att.admin_note += f"\n{stamped}"
                    else:
                        att.admin_note = stamped
                
                if attendance:
                    if action == 'waive':
                        first_in = attendance.first_punch_in_time
                        last_out = attendance.last_punch_out_time
                        admin_punch_note = None

                        if not first_in and not last_out:
                            first_in = _make_admin_dt(duty_start)
                            last_out = _make_admin_dt(duty_end)
                            attendance.first_punch_in_time = first_in
                            attendance.last_punch_out_time = last_out
                            admin_punch_note = 'Auto-filled punch in/out by admin for waived missed punch penalty'
                        elif first_in and not last_out:
                            last_out = _make_admin_dt(duty_end)
                            attendance.last_punch_out_time = last_out
                            admin_punch_note = 'Auto-filled punch out by admin for waived missed punch penalty'
                        elif last_out and not first_in:
                            first_in = _make_admin_dt(duty_start)
                            attendance.first_punch_in_time = first_in
                            admin_punch_note = 'Auto-filled punch in by admin for waived missed punch penalty'

                        if admin_punch_note:
                            attendance.status = 'full'
                            attendance.verification_status = 'verified'
                            attendance.verified_by = request.user if request.user.is_authenticated else attendance.verified_by
                            attendance.verified_at = timezone.now()

                            attendance.punch_records.all().delete()
                            if first_in:
                                PunchRecord.objects.create(
                                    attendance=attendance,
                                    punch_type='in',
                                    punch_time=first_in,
                                    note='Auto-filled by admin during missed punch waiver'
                                )
                            if last_out:
                                PunchRecord.objects.create(
                                    attendance=attendance,
                                    punch_type='out',
                                    punch_time=last_out,
                                    note='Auto-filled by admin during missed punch waiver'
                                )

                            _stamp_admin_note(attendance, admin_punch_note)

                    if action == 'waive':
                        _stamp_admin_note(attendance, f'Missed punch penalty waived on {timezone.now().strftime("%Y-%m-%d")}')
                    else:
                        _stamp_admin_note(attendance, f'Missed punch penalty deducted on {timezone.now().strftime("%Y-%m-%d")}')

                    attendance.save()
                    updated_count = 1
                    message = f'Successfully {action}d missed punch penalty for {date_str}'
                else:
                    if action == 'waive':
                        first_in = _make_admin_dt(duty_start)
                        last_out = _make_admin_dt(duty_end)
                        attendance = Attendance.objects.create(
                            user=user,
                            date=penalty_date,
                            status='full',
                            first_punch_in_time=first_in,
                            last_punch_out_time=last_out,
                            total_working_hours=0,
                            total_break_hours=0,
                            is_currently_on_break=False,
                            verification_status='verified',
                            verified_by=request.user if request.user.is_authenticated else None,
                            verified_at=timezone.now(),
                            admin_note=f'Missed punch penalty waived on {timezone.now().strftime("%Y-%m-%d")}\nAuto-filled punch in/out by admin for waived missed punch penalty',
                        )
                        if first_in:
                            PunchRecord.objects.create(
                                attendance=attendance,
                                punch_type='in',
                                punch_time=first_in,
                                note='Auto-filled by admin during missed punch waiver'
                            )
                        if last_out:
                            PunchRecord.objects.create(
                                attendance=attendance,
                                punch_type='out',
                                punch_time=last_out,
                                note='Auto-filled by admin during missed punch waiver'
                            )
                    else:
                        # Create a placeholder attendance row so the review action is persisted
                        # and the frontend can show the reviewed missed punch on reload.
                        attendance = Attendance.objects.create(
                            user=user,
                            date=penalty_date,
                            status='absent',
                            admin_note=f'Missed punch penalty deducted on {timezone.now().strftime("%Y-%m-%d")}')
                    updated_count = 1
                    message = f'Created and {action}d missed punch penalty for {date_str}'
        
        return Response({
            'success': True,
            'message': message or f'Successfully {action}d penalty for {date_str}',
            'data': {
                'employee_id': employee_id,
                'date': date_str,
                'penalty_type': penalty_type,
                'action': action,
                'updated_count': updated_count
            }
        }, status=status.HTTP_200_OK)
    
    except Employee.DoesNotExist:
        return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.exception('Error applying daily penalty action')
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
