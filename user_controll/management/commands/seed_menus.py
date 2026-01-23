# user_controll/management/commands/seed_menus.py
from django.core.management.base import BaseCommand
from user_controll.models import MenuItem


class Command(BaseCommand):
    help = 'Seed menu items matching your HR System structure with correct paths'

    def handle(self, *args, **options):
        # Clear old menu items to avoid conflicts
        self.stdout.write("Clearing existing menu items...")
        MenuItem.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("✓ Cleared existing menu items"))

        # Define your exact menu structure WITH CORRECT PATHS from App.jsx
        menus = [
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
                        "key": "hr_leave_main",
                        "path": "#",
                        "icon": "🗓️",
                        "order": 8,
                        "children": [
                            {
                                "name": "Leave Management",
                                "key": "hr_leave_management",
                                "path": "/hr/leave-management",
                                "icon": "🗓️",
                                "order": 1,
                            },
                        ],
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
                    {
                        "name": "HR Master",
                        "key": "hr_master",
                        "path": "#",
                        "icon": "⚙️",
                        "order": 10,
                        "children": [
                            {
                                "name": "Employee Management",
                                "key": "hr_master_employee",
                                "path": "/hr/master/employee-management",
                                "icon": "👥",
                                "order": 1,
                            },
                            {
                                "name": "Job Titles",
                                "key": "hr_master_job_titles",
                                "path": "/hr/master/job-titles",
                                "icon": "💼",
                                "order": 2,
                            },
                            {
                                "name": "Leave Types",
                                "key": "hr_master_leave_types",
                                "path": "/hr/master/leave-types",
                                "icon": "🗓️",
                                "order": 3,
                            },
                            {
                                "name": "Salary Certificate",
                                "key": "hr_master_salary_certificate",
                                "path": "/hr/master/salary-certificate",
                                "icon": "💰",
                                "order": 4,
                            },
                            {
                                "name": "Experience Certificate",
                                "key": "hr_master_experience_certificate",
                                "path": "/hr/master/experience-certificate",
                                "icon": "🎓",
                                "order": 5,
                            },
                            {
                                "name": "Deductions",
                                "key": "hr_master_deductions",
                                "path": "/hr/master/deductions",
                                "icon": "💸",
                                "order": 6,
                            },
                            {
                                "name": "Allowances",
                                "key": "hr_master_allowances",
                                "path": "/hr/master/allowances",
                                "icon": "💵",
                                "order": 7,
                            },
                            {
                                "name": "WhatsApp Admin",
                                "key": "hr_master_whatsapp_admin",
                                "path": "/hr/master/whatsapp-admin",
                                "icon": "📱",
                                "order": 8,
                            },
                        ],
                    },
                ],
            },

            # ------------------ USER MANAGEMENT ------------------
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

            # ------------------ PAYROLL ------------------
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

            # ------------------ MASTER DATA ------------------
            {
                "name": "Master Data",
                "key": "master",
                "path": "#",
                "icon": "⚙️",
                "order": 4,
                "children": [
                    {
                        "name": "Leave Master",
                        "key": "leave_master",
                        "path": "/master/leave-master",
                        "icon": "🗓️",
                        "order": 1,
                    },
                    {
                        "name": "Salary Deduction Master",
                        "key": "salary_deduction_master",
                        "path": "/master/salary-deduction-master",
                        "icon": "➖",
                        "order": 2,
                    },
                    {
                        "name": "Salary Allowance Master",
                        "key": "salary_allowance_master",
                        "path": "/master/salary-allowance-master",
                        "icon": "➕",
                        "order": 3,
                    },
                    {
                        "name": "WhatsApp Admin",
                        "key": "master_whatsapp_admin",
                        "path": "/master/whatsapp-admin",
                        "icon": "📱",
                        "order": 4,
                    },
                ],
            },
        ]

        created_count = 0
        updated_count = 0

        def create_or_update_menu(menu_data, parent=None):
            nonlocal created_count, updated_count

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
                created_count += 1
                indent = "  " * (1 if parent else 0)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{indent}✓ Created: {menu_data['name']:40} "
                        f"[{menu_data['key']:35}] -> {menu_data.get('path', '#')}"
                    )
                )
            else:
                menu.name = menu_data["name"]
                menu.path = menu_data.get("path", "")
                menu.icon = menu_data.get("icon", "")
                menu.parent = parent
                menu.order = menu_data.get("order", 0)
                menu.is_active = True
                menu.save()
                updated_count += 1
                indent = "  " * (1 if parent else 0)
                self.stdout.write(
                    self.style.WARNING(
                        f"{indent}⚠ Updated: {menu_data['name']:40} "
                        f"[{menu_data['key']:35}] -> {menu_data.get('path', '#')}"
                    )
                )

            # Process children
            for child_data in menu_data.get("children", []):
                create_or_update_menu(child_data, parent=menu)

        self.stdout.write("\n" + "=" * 110)
        self.stdout.write("Starting menu seed process...")
        self.stdout.write("=" * 110 + "\n")

        for menu_data in menus:
            create_or_update_menu(menu_data)

        self.stdout.write("\n" + "=" * 110)
        self.stdout.write(self.style.SUCCESS("✅ Process complete!"))
        self.stdout.write(self.style.SUCCESS(f"   - Created: {created_count} new items"))
        self.stdout.write(self.style.SUCCESS(f"   - Updated: {updated_count} existing items"))
        self.stdout.write("=" * 110 + "\n")
        
        # Verify HR Master structure
        self.stdout.write("\n🔍 VERIFYING HR MASTER STRUCTURE:")
        self.stdout.write("-" * 110)
        
        try:
            hr_master = MenuItem.objects.get(key='hr_master')
            children = hr_master.children.filter(is_active=True).order_by('order')
            self.stdout.write(self.style.SUCCESS(f"\n✅ HR Master found with {children.count()} children:"))
            for i, child in enumerate(children, 1):
                self.stdout.write(f"   {i}. {child.name} ({child.key}) - {child.path}")
            
            # Check if Allowances exists
            if children.filter(key='hr_master_allowances').exists():
                self.stdout.write(self.style.SUCCESS("\n✅ Allowances menu item found under HR Master!"))
            else:
                self.stdout.write(self.style.ERROR("\n❌ Allowances NOT found under HR Master!"))
                
        except MenuItem.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ HR Master menu not found!"))
        
        self.stdout.write("\n" + "=" * 110)
        self.stdout.write("\n💡 Next steps:")
        self.stdout.write("   1. Logout from application")
        self.stdout.write("   2. Clear browser cache: localStorage.clear() + sessionStorage.clear()")
        self.stdout.write("   3. Login again")
        self.stdout.write("   4. Check HR Management → HR Master → Allowances should be there!\n")
        self.stdout.write("=" * 110 + "\n")