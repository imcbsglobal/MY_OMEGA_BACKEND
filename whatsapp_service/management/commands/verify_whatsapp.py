# ============================================================================
# FILE 8: whatsapp_service/management/commands/verify_whatsapp.py
# ============================================================================

"""
Complete verification and testing for WhatsApp integration.

Usage:
    python manage.py verify_whatsapp
    python manage.py verify_whatsapp --send-test
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import requests
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Verify WhatsApp configuration and test sending'

    def add_arguments(self, parser):
        parser.add_argument(
            '--send-test',
            action='store_true',
            help='Actually send a test message'
        )

    def handle(self, *args, **options):
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('WhatsApp Integration Complete Verification'))
        self.stdout.write('=' * 80)
        self.stdout.write('')

        # Step 1: Check settings
        settings_ok = self.check_settings()
        
        # Step 2: Check admin numbers
        self.check_admin_config()
        
        # Step 3: Test API directly
        if settings_ok and options['send_test']:
            self.stdout.write('')
            response = self.prompt_yes_no('Send test message via direct API call?')
            if response:
                self.test_direct_api()
            
            self.stdout.write('')
            response = self.prompt_yes_no('Send test message via Django utils?')
            if response:
                self.test_django_utils()
        elif settings_ok:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('ℹ️  Add --send-test flag to actually send test messages'))
        
        self.stdout.write('')
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('Verification Complete'))
        self.stdout.write('=' * 80)

    def prompt_yes_no(self, question):
        """Prompt user for yes/no response"""
        response = input(f"{question} (y/n): ").lower().strip()
        return response in ['y', 'yes']

    def check_settings(self):
        """Verify all required settings"""
        self.stdout.write(self.style.HTTP_INFO('STEP 1: Settings Verification'))
        self.stdout.write('-' * 80)
        
        required_settings = {
            'WHATSAPP_PROVIDER': getattr(settings, 'WHATSAPP_PROVIDER', None),
            'DXING_API_URL': getattr(settings, 'DXING_API_URL', None),
            'DXING_SECRET': getattr(settings, 'DXING_SECRET', None),
            'DXING_ACCOUNT': getattr(settings, 'DXING_ACCOUNT', None),
        }
        
        all_good = True
        for key, value in required_settings.items():
            if value:
                if key == 'DXING_SECRET':
                    masked = '***' + value[-4:] if len(str(value)) > 4 else '***'
                    self.stdout.write(f"  ✓ {key}: {masked}")
                else:
                    self.stdout.write(f"  ✓ {key}: {value}")
            else:
                self.stdout.write(self.style.ERROR(f"  ✗ {key}: NOT SET"))
                all_good = False
        
        if not all_good:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('❌ Missing required settings!'))
            self.stdout.write('')
            self.stdout.write('Add these to your settings.py:')
            self.stdout.write('')
            self.stdout.write('    WHATSAPP_PROVIDER = "dxing"')
            self.stdout.write('    DXING_API_URL = "https://app.dxing.in/api/send/whatsapp"')
            self.stdout.write('    DXING_SECRET = "your_secret_from_dxing_dashboard"')
            self.stdout.write('    DXING_ACCOUNT = "your_account_id_from_dxing_dashboard"')
            return False
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ All settings are configured'))
        return True

    def check_admin_config(self):
        """Check admin numbers configuration"""
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('STEP 2: Admin Numbers Configuration'))
        self.stdout.write('-' * 80)
        
        try:
            from whatsapp_service import admin_numbers
            
            hr_admins = admin_numbers.get_hr_admin_numbers()
            managers = admin_numbers.get_manager_fallback_numbers()
            all_recipients = admin_numbers.get_all_notification_recipients()
            
            self.stdout.write(f"  HR Admins: {len(hr_admins)} configured")
            for num in hr_admins:
                self.stdout.write(f"    - {num}")
            
            self.stdout.write(f"  Managers: {len(managers)} configured")
            for num in managers:
                self.stdout.write(f"    - {num}")
            
            self.stdout.write(f"  Total unique recipients: {len(all_recipients)}")
            
            if not all_recipients:
                self.stdout.write('')
                self.stdout.write(self.style.WARNING('⚠️  No admin numbers configured!'))
                self.stdout.write('  Generic requests will fail without recipients.')
                self.stdout.write('  Edit whatsapp_service/admin_numbers.py')
            else:
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('✅ Admin numbers configured'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error loading admin_numbers: {e}'))

    def test_direct_api(self):
        """Test DXING API directly"""
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('STEP 3: Direct DXING API Test'))
        self.stdout.write('-' * 80)
        
        api_url = getattr(settings, 'DXING_API_URL')
        secret = getattr(settings, 'DXING_SECRET')
        account = getattr(settings, 'DXING_ACCOUNT')
        
        # Get test number from admin_numbers
        try:
            from whatsapp_service import admin_numbers
            recipients = admin_numbers.get_all_notification_recipients()
            if recipients:
                test_number = recipients[0]
            else:
                test_number = "918281561081"  # fallback
        except:
            test_number = "918281561081"
        
        # Normalize number (remove +)
        test_number = test_number.replace('+', '').replace(' ', '')
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        message = f"🔔 Direct API Test at {timestamp}"
        
        payload = {
            "secret": secret,
            "account": account,
            "recipient": test_number,
            "type": "text",
            "message": message,
            "priority": 1
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        self.stdout.write(f"  API URL: {api_url}")
        self.stdout.write(f"  Recipient: {test_number}")
        self.stdout.write(f"  Message: {message}")
        self.stdout.write('')
        self.stdout.write('  Sending POST request with JSON body...')
        
        try:
            response = requests.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=15
            )
            
            self.stdout.write('')
            self.stdout.write(f"  HTTP Status: {response.status_code}")
            
            try:
                data = response.json()
                self.stdout.write(f"  Response: {json.dumps(data, indent=2)}")
                
                # Check for success
                if response.ok and (data.get('status') == 200 or 'success' in str(data).lower()):
                    self.stdout.write('')
                    self.stdout.write(self.style.SUCCESS('✅ Message sent successfully!'))
                    self.stdout.write('  Check your phone or DXING dashboard for delivery')
                    
                    if 'data' in data and 'messageId' in data['data']:
                        self.stdout.write(f"  Message ID: {data['data']['messageId']}")
                else:
                    self.stdout.write('')
                    self.stdout.write(self.style.ERROR('❌ API returned error'))
                    self.stdout.write(f"  Error: {data.get('message', 'Unknown error')}")
                    self.print_common_errors()
                    
            except:
                self.stdout.write(f"  Response Text: {response.text}")
                if not response.ok:
                    self.stdout.write('')
                    self.stdout.write(self.style.ERROR('❌ Request failed'))
                    self.print_common_errors()
                
        except requests.Timeout:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('❌ Request timeout'))
            self.stdout.write('  Check your internet connection')
            
        except requests.ConnectionError as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'❌ Connection error: {e}'))
            self.stdout.write('  Check if the API URL is correct')
            
        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'❌ Unexpected error: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

    def test_django_utils(self):
        """Test through Django utils"""
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('STEP 4: Django Utils Test'))
        self.stdout.write('-' * 80)
        
        try:
            from whatsapp_service.utils import send_whatsapp_notification
            from whatsapp_service import admin_numbers
            
            # Get test number
            recipients = admin_numbers.get_all_notification_recipients()
            if recipients:
                test_number = recipients[0]
            else:
                test_number = "+918281561081"
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            message = f"🔔 Django Utils Test at {timestamp}"
            
            self.stdout.write(f"  Recipient: {test_number}")
            self.stdout.write(f"  Message: {message}")
            self.stdout.write('')
            self.stdout.write('  Calling send_whatsapp_notification...')
            
            result = send_whatsapp_notification(test_number, message)
            
            if result:
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS('✅ Success!'))
                self.stdout.write(f"  Result: {json.dumps(result, indent=2)}")
            else:
                self.stdout.write('')
                self.stdout.write(self.style.ERROR('❌ Function returned None'))
                self.stdout.write('  Check Django logs for error details')
                self.stdout.write('  Enable logging in settings.py to see full errors')
                
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Import error: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())

    def print_common_errors(self):
        """Print common error causes"""
        self.stdout.write('')
        self.stdout.write('  Common causes:')
        self.stdout.write('    1. Wrong DXING_SECRET or DXING_ACCOUNT')
        self.stdout.write('    2. DXING account not active or verified')
        self.stdout.write('    3. Insufficient balance in DXING account')
        self.stdout.write('    4. Invalid phone number format')
        self.stdout.write('    5. WhatsApp number not connected in DXING dashboard')
        self.stdout.write('')
        self.stdout.write('  Next steps:')
        self.stdout.write('    1. Log into your DXING dashboard at https://app.dxing.in')
        self.stdout.write('    2. Verify your account is active')
        self.stdout.write('    3. Check your API credentials match settings.py')
        self.stdout.write('    4. Ensure your WhatsApp number is connected')
        self.stdout.write('    5. Check message delivery logs in DXING dashboard')

