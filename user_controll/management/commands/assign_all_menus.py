# user_controll/management/commands/assign_all_menus.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from user_controll.models import MenuItem, UserMenuAccess

User = get_user_model()


class Command(BaseCommand):
    help = 'Assign all menus to a specific user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email to assign menus to')
        parser.add_argument(
            '--view-only',
            action='store_true',
            help='Assign with view permission only (no edit/delete)'
        )

    def handle(self, *args, **options):
        email = options['email']
        view_only = options.get('view_only', False)
        
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ User '{email}' not found!")
            )
            self.stdout.write("\nAvailable users:")
            for u in User.objects.all()[:10]:
                self.stdout.write(f"  - {u.email} ({u.name})")
            return
        
        # Get all menu items
        all_menus = MenuItem.objects.filter(is_active=True)
        
        if not all_menus.exists():
            self.stdout.write(
                self.style.WARNING("No menu items found! Run 'python manage.py seed_menus' first.")
            )
            return
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(f"User: {user.name} ({user.email})")
        self.stdout.write(f"Level: {user.user_level}")
        self.stdout.write(f"Total Menus: {all_menus.count()}")
        self.stdout.write("="*60 + "\n")
        
        # Delete existing assignments
        deleted_count = UserMenuAccess.objects.filter(user=user).count()
        UserMenuAccess.objects.filter(user=user).delete()
        
        if deleted_count > 0:
            self.stdout.write(f"🗑️  Removed {deleted_count} existing menu assignments\n")
        
        # Create new assignments
        created_count = 0
        assignments = []
        
        for menu in all_menus:
            assignments.append(
                UserMenuAccess(
                    user=user,
                    menu_item=menu,
                    can_view=True,
                    can_edit=False if view_only else True,
                    can_delete=False if view_only else True
                )
            )
            created_count += 1
            
            # Show progress for every 10 items
            if created_count % 10 == 0:
                self.stdout.write(f"  Processing... {created_count}/{all_menus.count()}")
        
        # Bulk create all assignments
        UserMenuAccess.objects.bulk_create(assignments)
        
        self.stdout.write("\n" + "="*60)
        if view_only:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully assigned {created_count} menus (VIEW ONLY)")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully assigned {created_count} menus (FULL ACCESS)")
            )
        self.stdout.write("="*60 + "\n")
        
        self.stdout.write("\n💡 Next steps:")
        self.stdout.write("   1. Have the user logout and login again")
        self.stdout.write("   2. Or use the User Control Panel to fine-tune permissions")
        self.stdout.write(f"   3. User can now access all {created_count} menu items\n")