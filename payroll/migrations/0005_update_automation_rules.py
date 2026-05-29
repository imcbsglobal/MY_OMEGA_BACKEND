# Generated migration to update AutomationRule choices
# Removes overtime, breaks, earlyOvertime and adds missed
# Changes Percentage to Percentage Per Day

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0004_automationrule'),
    ]

    operations = [
        migrations.AlterField(
            model_name='automationrule',
            name='rule_type',
            field=models.CharField(
                choices=[
                    ('late', 'Late Entry Rules'),
                    ('early', 'Early Exit Rules'),
                    ('missed', 'Punch Miss Rules'),
                ],
                max_length=20
            ),
        ),
        migrations.AlterField(
            model_name='automationrule',
            name='deduction_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('Fixed Amount', 'Fixed Amount'),
                    ('Percentage Per Day', 'Percentage Per Day'),
                    ('Half Day', 'Half Day'),
                    ('Full Day', 'Full Day'),
                ],
                max_length=20,
                null=True
            ),
        ),
    ]
