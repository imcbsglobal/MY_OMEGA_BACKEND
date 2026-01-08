# user_controll/management/commands/setup_complete_menu_system.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from user_controll.models import MenuItem, UserMenuAccess
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Complete menu system setup: seed menus + assign to user'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email to setup')
        parser.add_argument(
            '--skip-seed',
            action='store_true',
            help='Skip menu seeding (only assign existing menus)'
        )

    def handle(self, *args, **options):
        email = options['email']
        skip_seed = options.get('skip_seed', False)
        
        # Get user
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ User '{email}' not found!")
            )
            return

        self.stdout.write("\n" + "="*80)
        self.stdout.write("COMPLETE MENU SYSTEM SETUP")
        self.stdout.write("="*80)
        self.stdout.write(f"User: {user.name} ({user.email})")
        self.stdout.write(f"User Level: {user.user_level}")
        self.stdout.write("="*80 + "\n")

        # STEP 1: Seed Menus
        if not skip_seed:
            self.stdout.write("STEP 1: Seeding Menu Structure")
            self.stdout.write("-" * 80)
            
            # Clear existing
            old_count = MenuItem.objects.count()
            MenuItem.objects.all().delete()
            self.stdout.write(f"🗑️  Deleted {old_count} old menu items")
            
            # Seed new menus (matching App.jsx routes)
            menus = self._get_menu_structure()
            created = self._create_menus(menus)
            
            self.stdout.write(self.style.SUCCESS(f"✅ Created {created} menu items\n"))
        else:
            self.stdout.write(self.style.WARNING("⏭️  Skipping menu seed\n"))

        # STEP 2: Assign to User
        self.stdout.write("STEP 2: Assigning Menus to User")
        self.stdout.write("-" * 80)
        
        try:
            with transaction.atomic():
                # Delete old assignments
                old_assignments = UserMenuAccess.objects.filter(user=user).count()
                UserMenuAccess.objects.filter(user=user).delete()
                
                if old_assignments > 0:
                    self.stdout.write(f"🗑️  Deleted {old_assignments} old assignments")
                
                # Get all active menus
                all_menus = MenuItem.objects.filter(is_active=True)
                
                if not all_menus.exists():
                    self.stdout.write(
                        self.style.ERROR("❌ No active menus found!")
                    )
                    return
                
                # Create new assignments
                assignments = []
                for menu in all_menus:
                    assignments.append(
                        UserMenuAccess(
                            user=user,
                            menu_item=menu,
                            can_view=True,
                            can_edit=True,
                            can_delete=True
                        )
                    )
                
                UserMenuAccess.objects.bulk_create(assignments)
                
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Assigned {len(assignments)} menus to user")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error: {str(e)}")
            )
            return

        # STEP 3: Verify
        self.stdout.write("\nSTEP 3: Verification")
        self.stdout.write("-" * 80)
        
        total_menus = MenuItem.objects.filter(is_active=True).count()
        user_menus = UserMenuAccess.objects.filter(
            user=user, 
            menu_item__is_active=True
        ).count()
        
        self.stdout.write(f"Total Active Menus: {total_menus}")
        self.stdout.write(f"User Assignments: {user_menus}")
        
        if total_menus == user_menus:
            self.stdout.write(self.style.SUCCESS("✅ All menus assigned correctly!"))
        else:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Missing {total_menus - user_menus} assignments")
            )

        # STEP 4: Final Instructions
        self.stdout.write("\n" + "="*80)
        self.stdout.write("SETUP COMPLETE!")
        self.stdout.write("="*80)
        self.stdout.write("\n🎉 Menu system setup finished successfully!\n")
        self.stdout.write("📋 What the user needs to do now:\n")
        self.stdout.write("   1. LOGOUT from the application")
        self.stdout.write("   2. Open Browser DevTools (F12)")
        self.stdout.write("   3. Go to: Application → Local Storage")
        self.stdout.write("   4. Click 'Clear All' or run: localStorage.clear()")
        self.stdout.write("   5. LOGIN again")
        self.stdout.write("   6. All menus should now be visible in sidebar\n")
        self.stdout.write("="*80 + "\n")

    def _get_menu_structure(self):
        """Menu structure matching App.jsx routes"""
        return [
            {
                "name": "HR Management",
                "key": "hr",
                "path": "#",
                "icon": "👥",
                "order": 1,
                "children": [
                    {
                        "name": "Add CV",
                        "key": "hr_add_cv",
                        "path": "/hr/add-cv",
                        "icon": "📋",
                        "order": 1,
                    },
                    {
                        "name": "Interview Management",
                        "key": "hr_interview",
                        "path": "/hr/interview-management",
                        "icon": "👤",
                        "order": 2,
                    },
                    {
                        "name": "Offer Letter",
                        "key": "hr_offer_letter",
                        "path": "/hr/offer-letter",
                        "icon": "📄",
                        "order": 3,
                    },
                    {
                        "name": "Add Offer Letter",
                        "key": "hr_add_offer_letter",
                        "path": "/hr/add-offer-letter",
                        "icon": "➕",
                        "order": 4,
                    },
                    {
                        "name": "Employee Management",
                        "key": "hr_employee",
                        "path": "/hr/employee-management",
                        "icon": "👥",
                        "order": 5,
                    },
                    {
                        "name": "Add Employee",
                        "key": "hr_add_employee",
                        "path": "/hr/add-employee",
                        "icon": "➕",
                        "order": 6,
                    },
                    {
                        "name": "Attendance",
                        "key": "hr_attendance_main",
                        "path": "#",
                        "icon": "📊",
                        "order": 7,
                        "children": [
                            {
                                "name": "Attendance",
                                "key": "hr_attendance",
                                "path": "/hr/attendance",
                                "icon": "📊",
                                "order": 1,
                            },
                            {
                                "name": "Punch In/Out",
                                "key": "hr_punchinpunchout",
                                "path": "/hr/punchinpunchout",
                                "icon": "⏰",
                                "order": 2,
                            },
                        ],
                    },
                    {
                        "name": "Leave Management",
                        "key": "hr_leave_management",
                        "path": "/hr/leave-management",
                        "icon": "🗓️",
                        "order": 8,
                    },
                    {
                        "name": "Certificates",
                        "key": "hr_certificates",
                        "path": "#",
                        "icon": "🎓",
                        "order": 9,
                        "children": [
                            {
                                "name": "Experience Certificate",
                                "key": "hr_experience",
                                "path": "/hr/experience-certificate",
                                "icon": "🎓",
                                "order": 1,
                            },
                            {
                                "name": "Salary Certificate",
                                "key": "hr_salary",
                                "path": "/hr/salary-certificate",
                                "icon": "💰",
                                "order": 2,
                            },
                        ],
                    },
                ],
            },
            {
                "name": "User Management",
                "key": "user_management",
                "path": "#",
                "icon": "🧑",
                "order": 2,
                "children": [
                    {
                        "name": "User List",
                        "key": "user_list",
                        "path": "/user/list",
                        "icon": "📋",
                        "order": 1,
                    },
                    {
                        "name": "Add User",
                        "key": "user_add",
                        "path": "/user/add",
                        "icon": "➕",
                        "order": 2,
                    },
                    {
                        "name": "User Control Panel",
                        "key": "user_control",
                        "path": "/admin/user-control",
                        "icon": "🔐",
                        "order": 3,
                    },
                ],
            },
            {
                "name": "Payroll",
                "key": "payroll",
                "path": "#",
                "icon": "💰",
                "order": 3,
                "children": [
                    {
                        "name": "Payroll List",
                        "key": "payroll_list",
                        "path": "/payroll",
                        "icon": "📋",
                        "order": 1,
                    },
                    {
                        "name": "Process Payroll",
                        "key": "payroll_new",
                        "path": "/payroll/new",
                        "icon": "➕",
                        "order": 2,
                    },
                ],
            },
        ]

    def _create_menus(self, menus, parent=None):
        """Recursively create menu items"""
        count = 0
        for menu_data in menus:
            menu, created = MenuItem.objects.get_or_create(
                key=menu_data["key"],
                defaults={
                    "name": menu_data["name"],
                    "path": menu_data.get("path", ""),
                    "icon": menu_data.get("icon", ""),
                    "parent": parent,
                    "order": menu_data.get("order", 0),
                    "is_active": True,
                }
            )
            
            if created:
                count += 1
                self.stdout.write(f"  ✓ {menu_data['name']}")
            
            # Process children
            if menu_data.get("children"):
                count += self._create_menus(menu_data["children"], parent=menu)
        
        return count