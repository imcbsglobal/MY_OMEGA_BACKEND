import os
import sys
import django
from django.db import connections
from django.db.migrations.loader import MigrationLoader

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()
loader = MigrationLoader(connections['default'])
print('Applied migrations (sample):')
for m in sorted(loader.applied_migrations):
    print(m)
print('\nGraph nodes sample:')
for n in sorted(loader.graph.nodes)[:20]:
    print(n)
