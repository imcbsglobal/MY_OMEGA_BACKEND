import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
try:
    django.setup()
    from django.db import connection
    tables = connection.introspection.table_names()
    print('Found', len(tables), 'tables')
    print('hr_employee_leave_balance' in tables)
    if 'hr_employee_leave_balance' in tables:
        print('OK: table exists')
    else:
        print('MISSING: hr_employee_leave_balance not found')
except Exception as e:
    print('ERROR:', e)
    import traceback; traceback.print_exc()
