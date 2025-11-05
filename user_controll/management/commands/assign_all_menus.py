from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from user_controll.models import MenuItem, UserMenuAccess

User = get_user_model()


class Command(BaseCommand):
    help = 'Assign all menus to a specific user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to assign menus to')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"User '{username}' not found!")
            )
            return
        
        # Get all menu items
        all_menus = MenuItem.objects.filter(is_active=True)
        
        if not all_menus.exists():
            self.stdout.write(
                self.style.WARNING("No menu items found! Run 'python manage.py seed_menus' first.")
            )
            return
        
        # Delete existing assignments
        UserMenuAccess.objects.filter(user=user).delete()
        
        # Create new assignments
        created_count = 0
        for menu in all_menus:
            UserMenuAccess.objects.create(user=user, menu_item=menu)
            created_count += 1
            self.stdout.write(f"  ✓ Assigned: {menu.name}")
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(
            self.style.SUCCESS(f"✅ Successfully assigned {created_count} menus to '{username}'")
        )
        self.stdout.write("="*60 + "\n")