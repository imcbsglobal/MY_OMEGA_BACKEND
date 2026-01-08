# management/commands/check_employee_salary.py
# Run: python manage.py check_employee_salary

from django.core.management.base import BaseCommand
from employee_management.models import Employee


class Command(BaseCommand):
    help = 'Check where employee salary information is stored'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Checking Employee Salary Configuration...'))
        self.stdout.write('')
        
        employees = Employee.objects.all()[:5]  # Check first 5 employees
        
        if not employees:
            self.stdout.write(self.style.WARNING('No employees found in database'))
            return
        
        for emp in employees:
            self.stdout.write(self.style.HTTP_INFO(f'Employee: {emp.id}'))
            
            # Try to get name
            name = None
            if hasattr(emp, 'get_full_name') and callable(emp.get_full_name):
                name = emp.get_full_name()
            elif hasattr(emp, 'full_name'):
                name = emp.full_name
            elif hasattr(emp, 'name'):
                name = emp.name
            
            if name:
                self.stdout.write(f'  Name: {name}')
            
            # Check direct fields
            self.stdout.write('  Direct Fields:')
            for field in ['basic_salary', 'salary', 'base_salary']:
                if hasattr(emp, field):
                    value = getattr(emp, field)
                    if value:
                        self.stdout.write(self.style.SUCCESS(f'    ✓ {field}: ₹{value}'))
                    else:
                        self.stdout.write(f'    ✗ {field}: None')
            
            # Check job_info
            if hasattr(emp, 'job_info') and emp.job_info:
                self.stdout.write('  Job Info Fields:')
                for field in ['basic_salary', 'salary', 'base_salary']:
                    if hasattr(emp.job_info, field):
                        value = getattr(emp.job_info, field)
                        if value:
                            self.stdout.write(self.style.SUCCESS(f'    ✓ {field}: ₹{value}'))
                        else:
                            self.stdout.write(f'    ✗ {field}: None')
            
            # Check employment_details
            if hasattr(emp, 'employment_details') and emp.employment_details:
                self.stdout.write('  Employment Details Fields:')
                for field in ['basic_salary', 'salary', 'base_salary']:
                    if hasattr(emp.employment_details, field):
                        value = getattr(emp.employment_details, field)
                        if value:
                            self.stdout.write(self.style.SUCCESS(f'    ✓ {field}: ₹{value}'))
                        else:
                            self.stdout.write(f'    ✗ {field}: None')
            
            # Show all attributes (for debugging)
            self.stdout.write('  All Available Attributes:')
            attrs = [attr for attr in dir(emp) if not attr.startswith('_') and not callable(getattr(emp, attr))]
            salary_related = [attr for attr in attrs if 'salary' in attr.lower() or 'pay' in attr.lower()]
            if salary_related:
                for attr in salary_related:
                    value = getattr(emp, attr, None)
                    self.stdout.write(f'    {attr}: {value}')
            
            self.stdout.write('')
        
        self.stdout.write(self.style.SUCCESS('Diagnostic Complete!'))
        self.stdout.write('')
        self.stdout.write('If no salary fields show ✓, you need to set basic_salary for your employees.')