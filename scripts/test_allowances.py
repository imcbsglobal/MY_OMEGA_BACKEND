import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')

import django
from django.test import Client

django.setup()

c = Client()
resp = c.get('/api/payroll/allowances/')
print('status:', resp.status_code)
print('content:', resp.content[:1000])
if resp.status_code != 200:
    # also try alternate path
    resp2 = c.get('/api/payroll/payroll/allowances/')
    print('alt status:', resp2.status_code)
    print('alt content:', resp2.content[:1000])
