from django.contrib import admin
"""
Django management command to setup WhatsApp Admin Panel

Usage:
    python manage.py setup_whatsapp_admin
    python manage.py setup_whatsapp_admin --migrate-settings
    python manage.py setup_whatsapp_admin --create-defaults
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from whatsapp_service.models import WhatsAppConfiguration, AdminNumber, MessageTemplate


class Command(BaseCommand):
    help = 'Setup WhatsApp Admin Panel with initial configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--migrate-settings',
            action='store_true',
            help='Migrate configuration from settings.py to database'
        )
        parser.add_argument(
            '--create-defaults',
            action='store_true',
            help='Create default message templates'
        )

    def handle(self, *args, **options):
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('WhatsApp Admin Panel Setup'))
        self.stdout.write('=' * 80)
        self.stdout.write('')

        if options['migrate_settings']:
            self.migrate_settings()
        
        if options['create_defaults']:
            self.create_default_templates()
        
        if not options['migrate_settings'] and not options['create_defaults']:
            # Run both by default
            self.migrate_settings()
            self.create_default_templates()
        
        self.stdout.write('')
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('✅ Setup Complete!'))
        self.stdout.write('=' * 80)
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Access the admin panel at: /api/whatsapp/admin/')
        self.stdout.write('2. Add admin phone numbers')
        self.stdout.write('3. Test your configuration')
        self.stdout.write('')

    def migrate_settings(self):
        """Migrate WhatsApp configuration from settings.py to database"""
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 1: Migrating Configuration from settings.py'))
        self.stdout.write('-' * 80)

        try:
            # Check if configuration exists in settings.py
            api_url = getattr(settings, 'DXING_API_URL', None)
            api_secret = getattr(settings, 'DXING_SECRET', None)
            account_id = getattr(settings, 'DXING_ACCOUNT', None)
            priority = getattr(settings, 'DXING_DEFAULT_PRIORITY', 1)

            if not api_url or not api_secret or not account_id:
                self.stdout.write(self.style.WARNING(
                    '⚠️  No DXING configuration found in settings.py'
                ))
                self.stdout.write('Please add the following to your settings.py:')
                self.stdout.write('')
                self.stdout.write('    DXING_API_URL = "https://app.dxing.in/api/send/whatsapp"')
                self.stdout.write('    DXING_SECRET = "your_secret_key"')
                self.stdout.write('    DXING_ACCOUNT = "your_account_id"')
                self.stdout.write('    DXING_DEFAULT_PRIORITY = 1')
                return

            # Create or update configuration in database
            config, created = WhatsAppConfiguration.objects.get_or_create(
                provider='dxing',
                defaults={
                    'api_url': api_url,
                    'api_secret': api_secret,
                    'account_id': account_id,
                    'default_priority': priority,
                    'is_active': True
                }
            )

            if not created:
                # Update existing configuration
                config.api_url = api_url
                config.api_secret = api_secret
                config.account_id = account_id
                config.default_priority = priority
                config.is_active = True
                config.save()
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Updated DXING configuration in database'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Created DXING configuration in database'
                ))

            self.stdout.write('')
            self.stdout.write('Configuration details:')
            self.stdout.write(f'  Provider: {config.provider.upper()}')
            self.stdout.write(f'  API URL: {config.api_url}')
            self.stdout.write(f'  Account ID: {config.account_id}')
            self.stdout.write(f'  Secret: {"*" * 20}')
            self.stdout.write(f'  Priority: {config.default_priority}')
            self.stdout.write(f'  Status: {"Active" if config.is_active else "Inactive"}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error migrating settings: {str(e)}'))

    def create_default_templates(self):
        """Create default message templates"""
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 2: Creating Default Message Templates'))
        self.stdout.write('-' * 80)

        default_templates = [
            {
                'template_type': 'punch_in',
                'recipient_type': 'both',
                'template_text': '''📍 Attendance Alert

Employee: {employee_name}
Action: PUNCH IN
Time: {time}
Date: {date}
Location: {location}

Thank you!''',
                'is_active': True
            },
            {
                'template_type': 'punch_out',
                'recipient_type': 'both',
                'template_text': '''📍 Attendance Alert

Employee: {employee_name}
Action: PUNCH OUT
Time: {time}
Date: {date}
Location: {location}

Thank you!''',
                'is_active': True
            },
            {
                'template_type': 'leave_request',
                'recipient_type': 'both',
                'template_text': '''📋 Leave Request Submitted

Employee: {employee_name}
Type: {leave_type}
From: {from_date}
To: {to_date}
Days: {days}
Reason: {reason}

Status: Pending Approval''',
                'is_active': True
            },
            {
                'template_type': 'leave_approval',
                'recipient_type': 'employee',
                'template_text': '''✅ Leave Request APPROVED

Employee: {employee_name}
Type: {leave_type}
From: {from_date}
To: {to_date}
Days: {days}

Approved by: {approver_name}''',
                'is_active': True
            },
            {
                'template_type': 'leave_rejection',
                'recipient_type': 'employee',
                'template_text': '''❌ Leave Request REJECTED

Employee: {employee_name}
Type: {leave_type}
From: {from_date}
To: {to_date}
Days: {days}

Rejected by: {approver_name}
Reason: {reason}''',
                'is_active': True
            },
            {
                'template_type': 'late_request',
                'recipient_type': 'both',
                'template_text': '''⏰ Late Coming Request Submitted

Employee: {employee_name}
Date: {date}
Late By: {late_by}
Reason: {reason}

Status: Pending Approval''',
                'is_active': True
            },
            {
                'template_type': 'late_approval',
                'recipient_type': 'employee',
                'template_text': '''✅ Late Coming Request APPROVED

Employee: {employee_name}
Date: {date}
Late By: {late_by}
Reason: {reason}

Approved by: {approver_name}''',
                'is_active': True
            },
            {
                'template_type': 'late_rejection',
                'recipient_type': 'employee',
                'template_text': '''❌ Late Coming Request REJECTED

Employee: {employee_name}
Date: {date}
Late By: {late_by}
Reason: {reason}

Rejected by: {approver_name}''',
                'is_active': True
            },
            {
                'template_type': 'early_request',
                'recipient_type': 'both',
                'template_text': '''⏳ Early Going Request Submitted

Employee: {employee_name}
Date: {date}
Early By: {early_by}
Reason: {reason}

Status: Pending Approval''',
                'is_active': True
            },
            {
                'template_type': 'early_approval',
                'recipient_type': 'employee',
                'template_text': '''✅ Early Going Request APPROVED

Employee: {employee_name}
Date: {date}
Early By: {early_by}
Reason: {reason}

Approved by: {approver_name}''',
                'is_active': True
            },
            {
                'template_type': 'early_rejection',
                'recipient_type': 'employee',
                'template_text': '''❌ Early Going Request REJECTED

Employee: {employee_name}
Date: {date}
Early By: {early_by}
Reason: {reason}

Rejected by: {approver_name}''',
                'is_active': True
            },
            {
                'template_type': 'generic_notification',
                'recipient_type': 'both',
                'template_text': '''📱 Notification

Employee: {employee_name}
Date: {date}

{message}''',
                'is_active': True
            }
        ]

        created_count = 0
        updated_count = 0

        for template_data in default_templates:
            template, created = MessageTemplate.objects.update_or_create(
                template_type=template_data['template_type'],
                defaults={
                    'recipient_type': template_data['recipient_type'],
                    'template_text': template_data['template_text'],
                    'is_active': template_data['is_active']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'  ✅ Created: {template.get_template_type_display()}'
                ))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(
                    f'  ⚠️  Updated: {template.get_template_type_display()}'
                ))

        self.stdout.write('')
        self.stdout.write(f'Created {created_count} new templates')
        self.stdout.write(f'Updated {updated_count} existing templates')
        self.stdout.write(f'Total templates: {MessageTemplate.objects.count()}')