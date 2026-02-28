import os
import sys
from decimal import Decimal

# Ensure project path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
import django
django.setup()

# Allow the test client host so middleware doesn't reject requests
from django.conf import settings
allowed = list(getattr(settings, 'ALLOWED_HOSTS', []))
if 'testserver' not in allowed:
    allowed.append('testserver')
    settings.ALLOWED_HOSTS = allowed

from django.test import Client
from django.contrib.auth import get_user_model
from delivery_management.models import Delivery, DeliveryStop
from django.urls import reverse

User = get_user_model()

print('Finding a staff or superuser for force_login...')
user = User.objects.filter(is_active=True).order_by('-is_superuser', '-is_staff').first()
if not user:
    raise SystemExit('No active user found to authenticate as')

client = Client()
client.force_login(user)
print('Authenticated as', user)

# Find a delivery that is scheduled or in_progress
delivery = Delivery.objects.filter(status__in=['scheduled','in_progress']).first()
if not delivery:
    raise SystemExit('No delivery found for testing')

print('Using delivery:', delivery.id, delivery.delivery_number, delivery.status)

# If scheduled, start it
if delivery.status == 'scheduled':
    start_url = f'/delivery-management/deliveries/{delivery.id}/start/'
    resp = client.post(start_url, data={'start_location': 'Test Location'})
    print('Start response:', resp.status_code, getattr(resp, 'json', lambda: resp.content)())

# Get next stop (API is mounted under /api/)
next_url = f'/api/delivery-management/deliveries/{delivery.id}/next-stop/'
resp = client.get(next_url)
print('Next-stop response:', resp.status_code)
try:
    data = resp.json()
except Exception:
    data = resp.content
print(data)

if resp.status_code == 200 and isinstance(data, dict) and data.get('id'):
    stop_id = data['id']
    print('Found pending stop id', stop_id)
    # Patch the stop
    patch_url = f'/api/delivery-management/delivery-stops/{stop_id}/'
    payload = {
        'shop_name': data.get('shop_name') or 'Smoke Test Shop',
        'delivered_boxes': float(data.get('planned_boxes') or 1),
        'collected_amount': float(data.get('planned_amount') or 0),
        'status': 'delivered',
        'notes': 'Smoke test update'
    }
    resp2 = client.patch(patch_url, data=payload, content_type='application/json')
    print('Patch stop response:', resp2.status_code)
    try:
        print(resp2.json())
    except Exception:
        print(resp2.content)

    # Get next stop again
    resp3 = client.get(next_url)
    print('Next-stop after patch:', resp3.status_code)
    try:
        print(resp3.json())
    except Exception:
        print(resp3.content)
else:
    print('No pending stops to test patch flow. Received:', data)

# Fetch delivery summary
summary_url = f'/api/delivery-management/deliveries/{delivery.id}/summary/'
resp4 = client.get(summary_url)
print('Summary response:', resp4.status_code)
try:
    print(resp4.json())
except Exception:
    print(resp4.content)

print('Smoke test completed')
