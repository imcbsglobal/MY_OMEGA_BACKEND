# Generated migration to add start_time and end_time fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0002_warehousetask_completed_datetime_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='warehousetask',
            name='start_time',
            field=models.TimeField(blank=True, help_text='Task start time (HH:MM)', null=True),
        ),
        migrations.AddField(
            model_name='warehousetask',
            name='end_time',
            field=models.TimeField(blank=True, help_text='Task end time (HH:MM)', null=True),
        ),
    ]
