import os, django, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()
user = User.objects.filter(is_active=True).exclude(is_staff=True).first()
if not user:
    print('No non-staff active user found')
else:
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get('/api/delivery/my-deliveries/')
    print('Testing as user:', getattr(user, 'email', str(user)))
    print('Status code:', resp.status_code)
    try:
        data = resp.json()
        print('Response items:', len(data) if isinstance(data, list) else 'not-list')
        print(json.dumps(data, indent=2, default=str))
    except Exception:
        print('Raw content:', resp.content)
