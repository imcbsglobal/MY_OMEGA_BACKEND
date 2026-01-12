import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')

import django
from django.urls import get_resolver

django.setup()

def walk(patterns, prefix=''):
    for p in patterns:
        try:
            pat = getattr(p, 'pattern', p)
            name = getattr(p, 'name', None)
            print(prefix + str(pat), '->', name)
            sub = getattr(p, 'url_patterns', None)
            if sub:
                walk(sub, prefix + '  ')
        except Exception as e:
            print('ERROR', e, 'on', p)

if __name__ == '__main__':
    resolver = get_resolver()
    walk(resolver.url_patterns)
