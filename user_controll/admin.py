from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import MenuItem, UserMenuAccess


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["name", "key", "path", "parent", "order", "is_active"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name", "key", "path"]
    list_editable = ["order", "is_active"]
    ordering = ["parent__id", "order", "name"]
    
    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "key", "path", "icon")
        }),
        ("Hierarchy", {
            "fields": ("parent", "order")
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
    )


@admin.register(UserMenuAccess)
class UserMenuAccessAdmin(admin.ModelAdmin):
    list_display = ["user", "menu_item", "created_at"]
    list_filter = ["menu_item", "user"]
    search_fields = ["user__username", "user__email", "menu_item__name"]
    raw_id_fields = ["user", "menu_item"]
    
    def created_at(self, obj):
        return obj.id
    created_at.short_description = "Access ID"




from django.core.management.base import BaseCommand
from User.models import AppUser


class Command(BaseCommand):
    help = 'Make a user an admin'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email')
        parser.add_argument(
            '--super',
            action='store_true',
            help='Make Super Admin instead of Admin'
        )

    def handle(self, *args, **options):
        email = options['email']
        is_super = options.get('super', False)
        
        try:
            user = AppUser.objects.get(email__iexact=email)
        except AppUser.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'✗ User not found: {email}')
            )
            self.stdout.write('\nAvailable users:')
            for u in AppUser.objects.all():
                self.stdout.write(f'  - {u.email}')
            return

        # Set user level
        if is_super:
            user.user_level = 'Super Admin'
            user.is_superuser = True
        else:
            user.user_level = 'Admin'
        
        user.is_staff = True
        user.save()

        self.stdout.write("\n" + "="*60)
        self.stdout.write(
            self.style.SUCCESS(f'✅ Successfully updated {user.email}')
        )
        self.stdout.write(f'   User Level: {user.user_level}')
        self.stdout.write(f'   is_staff: {user.is_staff}')
        self.stdout.write(f'   is_superuser: {user.is_superuser}')
        self.stdout.write("="*60 + "\n")
        
        self.stdout.write(
            self.style.WARNING('\n⚠️  IMPORTANT: Clear browser storage and login again!')
        )
        self.stdout.write('   1. Open browser console (F12)')
        self.stdout.write('   2. Run: localStorage.clear()')
        self.stdout.write('   3. Login with your credentials\n')