from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.apps import apps


class Command(BaseCommand):
    help = "Migrate legacy employee.department CharField values into cv_management.Department and populate Employee.department M2M"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Do not write changes, only log what would be done')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        Employee = apps.get_model('employee_management', 'Employee')
        Department = apps.get_model('cv_management', 'Department')

        table_name = Employee._meta.db_table
        legacy_column = 'department'

        # Check if legacy column exists
        with connection.cursor() as cursor:
            try:
                cols = [field.name for field in connection.introspection.get_table_description(cursor, table_name)]
            except Exception:
                cols = []

        if legacy_column not in cols:
            self.stdout.write(self.style.WARNING(f"Legacy column '{legacy_column}' not found on {table_name}. Nothing to migrate."))
            return

        self.stdout.write(self.style.NOTICE(f"Found legacy column '{legacy_column}' on {table_name}. Beginning migration."))

        # Fetch rows with non-empty department
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT id, {legacy_column} FROM {table_name} WHERE {legacy_column} IS NOT NULL AND {legacy_column} != ''")
            rows = cursor.fetchall()

        if not rows:
            self.stdout.write(self.style.SUCCESS("No legacy department values found to migrate."))
            return

        self.stdout.write(self.style.NOTICE(f"Found {len(rows)} employees with legacy department values."))

        for emp_id, dept_value in rows:
            # Split comma-separated values, strip whitespace
            names = [s.strip() for s in str(dept_value).split(',') if s.strip()]
            if not names:
                continue

            self.stdout.write(f"Employee {emp_id}: will map departments: {names}")

            if dry_run:
                continue

            try:
                with transaction.atomic():
                    emp = Employee.objects.get(pk=emp_id)
                    dept_objs = []
                    for name in names:
                        dept_obj, created = Department.objects.get_or_create(name=name)
                        dept_objs.append(dept_obj)
                    # Set M2M
                    emp.department.set(dept_objs)
                    self.stdout.write(self.style.SUCCESS(f"Employee {emp_id}: linked to departments {', '.join([d.name for d in dept_objs])}"))
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f"Failed to migrate employee {emp_id}: {exc}"))

        self.stdout.write(self.style.SUCCESS('Migration completed.'))
