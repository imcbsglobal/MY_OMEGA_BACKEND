# user_controll/management/commands/assign_approval_permissions.py
from django.core.management.base import BaseCommand
from User.models import AppUser
from user_controll.models import ApprovalCategory, UserApprovalPermission


class Command(BaseCommand):
    help = 'Assign approval permissions to users'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email')
        parser.add_argument(
            '--all',
            action='store_true',
            help='Assign all approval categories'
        )
        parser.add_argument(
            '--categories',
            nargs='+',
            type=str,
            help='Category keys to assign (e.g., attendance_approval leave_approval)'
        )
        parser.add_argument(
            '--approve-only',
            action='store_true',
            help='Grant only approve permission (not reject or view_all)'
        )

    def handle(self, *args, **options):
        email = options['email']
        assign_all = options.get('all', False)
        category_keys = options.get('categories', [])
        approve_only = options.get('approve_only', False)

        # Find user
        try:
            user = AppUser.objects.get(email__iexact=email)
        except AppUser.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ User not found: {email}')
            )
            self.stdout.write('\nAvailable users:')
            for u in AppUser.objects.all()[:10]:
                self.stdout.write(f'  - {u.email} ({u.name})')
            return

        self.stdout.write("\n" + "="*60)
        self.stdout.write(f"User: {user.name} ({user.email})")
        self.stdout.write(f"Level: {user.user_level}")
        self.stdout.write("="*60 + "\n")

        # Check if admin
        if user.user_level in ('Super Admin', 'Admin'):
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  This user is an Admin and already has ALL approval permissions.'
                )
            )
            self.stdout.write('   No need to assign permissions individually.')
            return

        # Assign permissions
        if assign_all:
            # Assign all active categories
            all_categories = ApprovalCategory.objects.filter(is_active=True)
            
            if not all_categories.exists():
                self.stdout.write(
                    self.style.ERROR('❌ No categories found! Run: python manage.py seed_approval_categories')
                )
                return
            
            # Clear existing assignments
            UserApprovalPermission.objects.filter(user=user).delete()
            
            # Assign all
            created = 0
            for category in all_categories:
                UserApprovalPermission.objects.create(
                    user=user,
                    category=category,
                    can_approve=True,
                    can_reject=False if approve_only else True,
                    can_view_all=False if approve_only else True
                )
                created += 1
                self.stdout.write(f"✓ {category.name}")
            
            self.stdout.write("\n" + "="*60)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Assigned ALL {created} approval categories to {user.name}')
            )
            if approve_only:
                self.stdout.write(
                    self.style.WARNING('   (Approve permission only)')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('   (Full permissions: Approve + Reject + View All)')
                )
            self.stdout.write("="*60 + "\n")
        
        elif category_keys:
            # Assign specific categories by keys
            assigned = 0
            not_found = []
            
            for key in category_keys:
                try:
                    category = ApprovalCategory.objects.get(key=key, is_active=True)
                    
                    # Create or update assignment
                    perm, created = UserApprovalPermission.objects.update_or_create(
                        user=user,
                        category=category,
                        defaults={
                            'can_approve': True,
                            'can_reject': False if approve_only else True,
                            'can_view_all': False if approve_only else True
                        }
                    )
                    
                    assigned += 1
                    status_text = "Created" if created else "Updated"
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {status_text}: {category.name}')
                    )
                
                except ApprovalCategory.DoesNotExist:
                    not_found.append(key)
            
            self.stdout.write("\n" + "="*60)
            if assigned > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Assigned {assigned} approval categories')
                )
                if approve_only:
                    self.stdout.write(
                        self.style.WARNING('   (Approve permission only)')
                    )
            if not_found:
                self.stdout.write(
                    self.style.ERROR(f'❌ Not found: {", ".join(not_found)}')
                )
                self.stdout.write('\nAvailable category keys:')
                for cat in ApprovalCategory.objects.filter(is_active=True):
                    self.stdout.write(f'  - {cat.key}: {cat.name}')
            self.stdout.write("="*60 + "\n")
        
        else:
            self.stdout.write(
                self.style.ERROR('❌ No categories specified!')
            )
            self.stdout.write('\nUsage:')
            self.stdout.write(f'  python manage.py assign_approval_permissions {email} --all')
            self.stdout.write(f'  python manage.py assign_approval_permissions {email} --categories attendance_approval leave_approval')
            self.stdout.write(f'  python manage.py assign_approval_permissions {email} --all --approve-only')