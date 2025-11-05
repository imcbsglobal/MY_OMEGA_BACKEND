from django.core.management.base import BaseCommand
from User.models import AppUser
from user_controll.models import UserMenuAccess


class Command(BaseCommand):
    help = 'List all users with their levels and menu counts'

    def handle(self, *args, **options):
        users = AppUser.objects.all().order_by('user_level', 'name')
        
        if not users.exists():
            self.stdout.write(
                self.style.WARNING('No users found in database')
            )
            return

        self.stdout.write("\n" + "="*80)
        self.stdout.write(f"{'EMAIL':<35} {'NAME':<20} {'LEVEL':<15} {'MENUS':<10}")
        self.stdout.write("="*80)

        for user in users:
            if user.user_level in ('Super Admin', 'Admin'):
                menu_count = "ALL"
            else:
                menu_count = str(UserMenuAccess.objects.filter(user=user).count())
            
            level_color = self.style.ERROR if user.user_level == 'Super Admin' else \
                         self.style.WARNING if user.user_level == 'Admin' else \
                         self.style.SUCCESS
            
            self.stdout.write(
                f"{user.email:<35} {user.name:<20} "
                f"{level_color(user.user_level):<15} {menu_count:<10}"
            )

        self.stdout.write("="*80)
        self.stdout.write(f"\nTotal users: {users.count()}")
        self.stdout.write(f"  - Super Admin: {users.filter(user_level='Super Admin').count()}")
        self.stdout.write(f"  - Admin: {users.filter(user_level='Admin').count()}")
        self.stdout.write(f"  - User: {users.filter(user_level='User').count()}")
        self.stdout.write("\n")