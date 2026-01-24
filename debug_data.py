import os
import django
from django.db import connection

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myomega_backend.settings")
django.setup()

def count_rows():
    with connection.cursor() as cursor:
        try:
            cursor.execute("SELECT COUNT(*) FROM master_leavemaster")
            master_count = cursor.fetchone()[0]
            print(f"master_leavemaster count: {master_count}")
        except Exception as e:
            print(f"Error querying master_leavemaster: {e}")

        try:
            cursor.execute("SELECT COUNT(*) FROM hr_leave_master")
            hr_count = cursor.fetchone()[0]
            print(f"hr_leave_master count: {hr_count}")
        except Exception as e:
            print(f"Error querying hr_leave_master: {e}")

if __name__ == "__main__":
    count_rows()
