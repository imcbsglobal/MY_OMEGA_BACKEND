from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('HR', '0007_alter_earlyrequest_unique_together'),
        ('master', '__latest__'),  # Make sure master app exists
    ]

    operations = [
        # Add is_leave field
        migrations.AddField(
            model_name='attendance',
            name='is_leave',
            field=models.BooleanField(default=False, help_text='Whether this day is a leave day'),
        ),
        # Add leave_request field
        migrations.AddField(
            model_name='attendance',
            name='leave_request',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='attendances',
                to='HR.leaverequest',
                help_text='Associated leave request if applicable'
            ),
        ),
        # Add leave_master field
        migrations.AddField(
            model_name='attendance',
            name='leave_master',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='attendances',
                to='master.leavemaster',
                help_text='Leave type from master if applicable'
            ),
        ),
        # Add is_paid_day field
        migrations.AddField(
            model_name='attendance',
            name='is_paid_day',
            field=models.BooleanField(default=True, help_text='For payroll: whether this day is paid'),
        ),
    ]