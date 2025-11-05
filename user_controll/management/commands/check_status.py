from django.core.management.base import BaseCommand
from User.models import AppUser
from user_controll.models import MenuItem, UserMenuAccess


class Command(BaseCommand):
    help = 'Check system status and show what needs to be done'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write("🔍 SYSTEM STATUS CHECK")
        self.stdout.write("="*80 + "\n")

        # Check 1: Menus
        menu_count = MenuItem.objects.filter(is_active=True).count()
        if menu_count == 0:
            self.stdout.write(
                self.style.ERROR("❌ No menus found!")
            )
            self.stdout.write(
                self.style.WARNING("   → Run: python manage.py seed_menus\n")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Menus: {menu_count} active menus found")
            )
            root_menus = MenuItem.objects.filter(is_active=True, parent__isnull=True)
            for root in root_menus:
                children = MenuItem.objects.filter(parent=root, is_active=True).count()
                self.stdout.write(f"   📁 {root.name} ({children} children)")
            self.stdout.write("")

        # Check 2: Users
        user_count = AppUser.objects.count()
        if user_count == 0:
            self.stdout.write(
                self.style.ERROR("❌ No users found!")
            )
            self.stdout.write(
                self.style.WARNING("   → Create users via User List page or admin panel\n")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Users: {user_count} users found")
            )
            
            # Count by level
            super_admins = AppUser.objects.filter(user_level='Super Admin').count()
            admins = AppUser.objects.filter(user_level='Admin').count()
            users = AppUser.objects.filter(user_level='User').count()
            
            if super_admins > 0:
                self.stdout.write(f"   👑 Super Admin: {super_admins}")
            if admins > 0:
                self.stdout.write(f"   🔑 Admin: {admins}")
            if users > 0:
                self.stdout.write(f"   👤 User: {users}")
            self.stdout.write("")

        # Check 3: Regular users without menu assignments
        regular_users = AppUser.objects.filter(user_level='User')
        if regular_users.exists():
            self.stdout.write("📋 Regular Users Menu Status:")
            needs_assignment = []
            
            for user in regular_users:
                # FIX: Use user_id instead of user object
                menu_count = UserMenuAccess.objects.filter(user_id=user.id).count()
                if menu_count == 0:
                    needs_assignment.append(user)
                    self.stdout.write(
                        self.style.WARNING(f"   ⚠️  {user.email} ({user.name}) - No menus assigned!")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✅ {user.email} ({user.name}) - {menu_count} menus")
                    )
            
            if needs_assignment:
                self.stdout.write("\n" + self.style.ERROR(f"❌ {len(needs_assignment)} users need menu assignments!"))
                self.stdout.write(self.style.WARNING("\nTo assign menus:"))
                for user in needs_assignment[:3]:  # Show first 3
                    self.stdout.write(f"   → python manage.py assign_user_menus {user.email} --all")
                if len(needs_assignment) > 3:
                    self.stdout.write(f"   ... and {len(needs_assignment) - 3} more")
            self.stdout.write("")

        # Check 4: Admins (they don't need assignments)
        admin_users = AppUser.objects.filter(user_level__in=['Super Admin', 'Admin'])
        if admin_users.exists():
            self.stdout.write(
                self.style.SUCCESS(f"✅ Admin Users: {admin_users.count()} (automatically have ALL menus)")
            )
            for user in admin_users:
                self.stdout.write(f"   🔓 {user.email} ({user.name}) - {user.user_level}")
            self.stdout.write("")

        # Summary and next steps
        self.stdout.write("="*80)
        self.stdout.write("📝 NEXT STEPS:")
        self.stdout.write("="*80 + "\n")

        if menu_count == 0:
            self.stdout.write("1️⃣  Seed the menus:")
            self.stdout.write("   python manage.py seed_menus\n")
        
        regular_without_menus = []
        for user in AppUser.objects.filter(user_level='User'):
            # FIX: Use user_id instead of user object
            if UserMenuAccess.objects.filter(user_id=user.id).count() == 0:
                regular_without_menus.append(user)
        
        if regular_without_menus:
            self.stdout.write("2️⃣  Assign menus to regular users:")
            for user in regular_without_menus[:3]:
                self.stdout.write(f"   python manage.py assign_user_menus {user.email} --all")
            self.stdout.write("")

        self.stdout.write("3️⃣  Clear browser storage and login:")
        self.stdout.write("   Open browser console (F12) and run:")
        self.stdout.write("   localStorage.clear()")
        self.stdout.write("   Then login with your credentials\n")

        self.stdout.write("4️⃣  View detailed user menus:")
        if user_count > 0:
            sample_user = AppUser.objects.first()
            self.stdout.write(f"   python manage.py show_user_menus {sample_user.email}\n")

        self.stdout.write("="*80)
        self.stdout.write("✨ Status check complete!")
        self.stdout.write("="*80 + "\n")