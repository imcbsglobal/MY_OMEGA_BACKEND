from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee_management', '0008_employee_address_employee_date_of_birth_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='work_type',
            field=models.CharField(
                blank=True,
                choices=[('in_house', 'In House'), ('out_house', 'Out House')],
                help_text='Whether the employee works in-house or out-house',
                max_length=20,
                null=True,
                verbose_name='Work Type',
            ),
        ),
    ]
