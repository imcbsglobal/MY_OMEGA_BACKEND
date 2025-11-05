from django.core.management.base import BaseCommand
from User.models import AppUser
from user_controll.models import MenuItem, UserMenuAccess


class Command(BaseCommand):
    help = 'Assign menus to existing users by email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email')
        parser.add_argument(
            '--all', 
            action='store_true', 
            help='Assign all menus'
        )
        parser.add_argument(
            '--keys',
            nargs='+',
            type=str,
            help='Menu keys to assign (e.g., hr_interview hr_attendance)'
        )

    def handle(self, *args, **options):
        email = options['email']
        assign_all = options.get('all', False)
        menu_keys = options.get('keys', [])

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
                    '⚠️  This user is an Admin and already has access to ALL menus.'
                )
            )
            self.stdout.write('   No need to assign menus individually.')
            return

        # Assign menus
        if assign_all:
            # Assign all active menus
            all_menus = MenuItem.objects.filter(is_active=True)
            
            if not all_menus.exists():
                self.stdout.write(
                    self.style.ERROR('❌ No menus found! Run: python manage.py seed_menus')
                )
                return
            
            # Clear existing assignments
            UserMenuAccess.objects.filter(user=user).delete()
            
            # Assign all
            created = 0
            for menu in all_menus:
                UserMenuAccess.objects.create(user=user, menu_item=menu)
                created += 1
                indent = "  " if menu.parent else ""
                self.stdout.write(f"{indent}✓ {menu.name}")
            
            self.stdout.write("\n" + "="*60)
            self.stdout.write(
                self.style.SUCCESS(f'✅ Assigned ALL {created} menus to {user.name}')
            )
            self.stdout.write("="*60 + "\n")
        
        elif menu_keys:
            # Assign specific menus by keys
            assigned = 0
            not_found = []
            
            for key in menu_keys:
                try:
                    menu = MenuItem.objects.get(key=key, is_active=True)
                    
                    # Create assignment
                    _, created = UserMenuAccess.objects.get_or_create(
                        user=user,
                        menu_item=menu
                    )
                    
                    if created:
                        assigned += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Assigned: {menu.name}')
                        )
                    
                    # Also assign parent if exists
                    if menu.parent:
                        parent_access, parent_created = UserMenuAccess.objects.get_or_create(
                            user=user,
                            menu_item=menu.parent
                        )
                        if parent_created:
                            assigned += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'✓ Auto-assigned parent: {menu.parent.name}')
                            )
                
                except MenuItem.DoesNotExist:
                    not_found.append(key)
            
            self.stdout.write("\n" + "="*60)
            if assigned > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Assigned {assigned} menus')
                )
            if not_found:
                self.stdout.write(
                    self.style.ERROR(f'❌ Not found: {", ".join(not_found)}')
                )
                self.stdout.write('\nAvailable menu keys:')
                for m in MenuItem.objects.filter(is_active=True):
                    indent = "  " if m.parent else ""
                    self.stdout.write(f'  {indent}- {m.key}')
            self.stdout.write("="*60 + "\n")
        
        else:
            self.stdout.write(
                self.style.ERROR('❌ No menus specified!')
            )
            self.stdout.write('\nUsage:')
            self.stdout.write(f'  python manage.py assign_user_menus {email} --all')
            self.stdout.write(f'  python manage.py assign_user_menus {email} --keys hr_interview hr_attendance')
