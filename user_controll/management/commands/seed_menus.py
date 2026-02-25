# user_controll/management/commands/seed_menus.py
from django.core.management.base import BaseCommand
from user_controll.models import MenuItem


class Command(BaseCommand):
    help = 'Seed menu items matching the Navbar sidebar structure'

    def handle(self, *args, **options):
        # Clear old menu items to avoid conflicts
        self.stdout.write("Clearing existing menu items...")
        MenuItem.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("✓ Cleared existing menu items"))

        # Define your exact menu structure
        menus = [
            # ------------------ HR MANAGEMENT ------------------
            {
                "name": "HR Management",
                "key": "hr",
                "path": "#",
                "icon": "👥",
                "order": 1,
                "children": [
                    {
                        "name": "Recruitment",
                        "key": "hr_recruitment",
                        "path": "#",
                        "icon": "👤",
                        "order": 1,
                        "children": [
                            {
                                "name": "CV Management",
                                "key": "hr_cv_management",
                                "path": "/cv-management",
                                "icon": "📋",
                                "order": 1,
                            },
                            {
                                "name": "Interview Management",
                                "key": "hr_interview",
                                "path": "/interview-management",
                                "icon": "👤",
                                "order": 2,
                            },
                            {
                                "name": "Offer Letter",
                                "key": "hr_offer_letter",
                                "path": "/offer-letter",
                                "icon": "📄",
                                "order": 3,
                            },
                        ],
                    },
                    {
                        "name": "Attendance Management",
                        "key": "hr_attendance",
                        "path": "/attendance-management",
                        "icon": "📊",
                        "order": 2,
                    },
                    {
                        "name": "Punch In/Punch Out",
                        "key": "hr_punchinpunchout",
                        "path": "/punch-in-out",
                        "icon": "⏰",
                        "order": 3,
                    },
                    {
                        "name": "HR Master",
                        "key": "hr_master",
                        "path": "#",
                        "icon": "⚙️",
                        "order": 4,
                        "children": [
                            {
                                "name": "Employee Management",
                                "key": "hr_employee",
                                "path": "/employee-management",
                                "icon": "👥",
                                "order": 1,
                            },
                            {
                                "name": "Job Titles",
                                "key": "hr_master_job_titles",
                                "path": "/master/job-titles",
                                "icon": "💼",
                                "order": 2,
                            },
                            {
                                "name": "Leave Types",
                                "key": "hr_master_leave_types",
                                "path": "/master/leave-types",
                                "icon": "🗓️",
                                "order": 3,
                            },
                            {
                                "name": "Salary Certificate",
                                "key": "hr_salary",
                                "path": "/salary-certificate",
                                "icon": "💰",
                                "order": 4,
                            },
                            {
                                "name": "Experience Certificate",
                                "key": "hr_experience",
                                "path": "/experience-certificate",
                                "icon": "🎓",
                                "order": 5,
                            },
                            {
                                "name": "Deductions",
                                "key": "hr_master_deductions",
                                "path": "/master/deductions",
                                "icon": "💸",
                                "order": 6,
                            },
                            {
                                "name": "Allowences",
                                "key": "hr_master_allowances",
                                "path": "/master/allowences",
                                "icon": "💵",
                                "order": 7,
                            },
                            {
                                "name": "WhatsApp Admin",
                                "key": "hr_master_whatsapp",
                                "path": "/master/whatsapp-admin",
                                "icon": "📱",
                                "order": 8,
                            },
                            {
                                "name": "Office Setup",
                                "key": "hr_master_office_setup",
                                "path": "/hr/master/office-setup",
                                "icon": "🏢",
                                "order": 9,
                            },
                        ],
                    },
                    {
                        "name": "Leave Management",
                        "key": "hr_leave_main",
                        "path": "#",
                        "icon": "🗓️",
                        "order": 5,
                        "children": [
                            {
                                "name": "Leave List",
                                "key": "hr_leave_list",
                                "path": "/leave-management/leave-list",
                                "icon": "📋",
                                "order": 1,
                            },
                            {
                                "name": "Early List",
                                "key": "hr_early_list",
                                "path": "/leave-management/early-list",
                                "icon": "⏰",
                                "order": 2,
                            },
                            {
                                "name": "Late List",
                                "key": "hr_late_list",
                                "path": "/leave-management/late-list",
                                "icon": "⏰",
                                "order": 3,
                            },
                        ],
                    },
                    {
                        "name": "Request",
                        "key": "hr_request",
                        "path": "#",
                        "icon": "📝",
                        "order": 6,
                        "children": [
                            {
                                "name": "Leave Request",
                                "key": "hr_request_leave",
                                "path": "/hr/request/leave",
                                "icon": "📋",
                                "order": 1,
                            },
                            {
                                "name": "Late Request",
                                "key": "hr_request_late",
                                "path": "/hr/request/late",
                                "icon": "⏰",
                                "order": 2,
                            },
                            {
                                "name": "Early Request",
                                "key": "hr_request_early",
                                "path": "/hr/request/early",
                                "icon": "⏰",
                                "order": 3,
                            },
                        ],
                    },
                    {
                        "name": "Payroll",
                        "key": "hr_payroll",
                        "path": "#",
                        "icon": "💰",
                        "order": 7,
                        "children": [
                            {
                                "name": "Payroll",
                                "key": "hr_payroll_processing",
                                "path": "/payroll",
                                "icon": "💰",
                                "order": 1,
                            },
                            {
                                "name": "Payslip",
                                "key": "hr_payslip",
                                "path": "/payslip",
                                "icon": "📄",
                                "order": 2,
                            },
                        ],
                    },
                ],
            },

            # ------------------ VEHICLE MANAGEMENT ------------------
            {
                "name": "Vehicle Management",
                "key": "vehicle",
                "path": "#",
                "icon": "🚗",
                "order": 2,
                "children": [
                    {
                        "name": "Fuel Management",
                        "key": "vehicle_fuel",
                        "path": "/vehicle/fuel-management",
                        "icon": "⛽",
                        "order": 1,
                    },
                    {
                        "name": "Travel",
                        "key": "vehicle_travel",
                        "path": "/vehicle/travel",
                        "icon": "🗺️",
                        "order": 2,
                    },
                    {
                        "name": "Challan",
                        "key": "vehicle_challan",
                        "path": "/vehicle/challan",
                        "icon": "📋",
                        "order": 3,
                    },
                ],
            },

            # ------------------ TARGET MANAGEMENT ------------------
            {
                "name": "Target Management",
                "key": "target_management",
                "path": "#",
                "icon": "🎯",
                "order": 3,
                "children": [
                    {
                        "name": "My Targets",
                        "key": "target_my_targets",
                        "path": "#",
                        "icon": "🎯",
                        "order": 1,
                        "children": [
                            {
                                "name": "View My Targets",
                                "key": "target_view_my_targets",
                                "path": "/target/my-targets",
                                "icon": "👁️",
                                "order": 1,
                            },
                        ],
                    },
                        {
                            "name": "Marketing",
                            "key": "target_marketing",
                            "path": "#",
                            "icon": "📢",
                            "order": 1.5,
                            "children": [
                                {
                                    "name": "Marketing Assign",
                                    "key": "target_marketing_assign",
                                    "path": "/target/marketing/assign",
                                    "icon": "📢",
                                    "order": 1,
                                },
                                {
                                    "name": "Marketing View",
                                    "key": "target_marketing_view",
                                    "path": "/target/marketing/view",
                                    "icon": "📢",
                                    "order": 2,
                                },
                            ],
                        },
                    {
                        "name": "Sales",
                        "key": "target_route",
                        "path": "#",
                        "icon": "🗺️",
                        "order": 2,
                        "children": [
                            {
                                "name": "Assign Route Target",
                                "key": "target_route_assign",
                                "path": "/target/route/assign",
                                "icon": "➕",
                                "order": 1,
                            },
                            {
                                "name": "Route Target List",
                                "key": "target_route_list",
                                "path": "/target/route/list",
                                "icon": "📋",
                                "order": 2,
                            },
                            {
                                "name": "Route Performance",
                                "key": "target_route_performance",
                                "path": "/target/route/performance",
                                "icon": "📊",
                                "order": 3,
                            },
                        ],
                    },
                    {
                        "name": "Call Targets",
                        "key": "target_call",
                        "path": "#",
                        "icon": "📞",
                        "order": 3,
                        "children": [
                            {
                                "name": "Assign Call Target",
                                "key": "target_call_assign",
                                "path": "/target/call/assign",
                                "icon": "➕",
                                "order": 1,
                            },
                            {
                                "name": "Call Target List",
                                "key": "target_call_list",
                                "path": "/target/call/list",
                                "icon": "📋",
                                "order": 2,
                            },
                            {
                                "name": "Call Performance",
                                "key": "target_call_performance",
                                "path": "/target/call/performance",
                                "icon": "📊",
                                "order": 3,
                            },
                        ],
                    },
                    {
                        "name": "Master Data",
                        "key": "target_master",
                        "path": "#",
                        "icon": "⚙️",
                        "order": 4,
                        "children": [
                            {
                                "name": "Routes",
                                "key": "target_master_routes",
                                "path": "/target/master/routes",
                                "icon": "🗺️",
                                "order": 1,
                            },
                            {
                                "name": "Products",
                                "key": "target_master_products",
                                "path": "/target/master/products",
                                "icon": "📦",
                                "order": 2,
                            },
                        ],
                    },
                ],
            },

            # ------------------ WAREHOUSE MANAGEMENT ------------------
            {
                "name": "Warehouse Management",
                "key": "warehouse_management",
                "path": "/under-construction",
                "icon": "🏭",
                "order": 4,
            },

            # ------------------ DELIVERY MANAGEMENT ------------------
            {
                "name": "Delivery Management",
                "key": "delivery_management",
                "path": "#",
                "icon": "🚚",
                "order": 5,
                "children": [
                    {
                        "name": "List Deliveries",
                        "key": "delivery_list",
                        "path": "/delivery-management/deliveries",
                        "icon": "📋",
                        "order": 1,
                    },
                    {
                        "name": "Create Delivery",
                        "key": "delivery_create",
                        "path": "/delivery-management/deliveries/new",
                        "icon": "➕",
                        "order": 2,
                    },
                    {
                        "name": "Employee Delivery View",
                        "key": "delivery_employee_view",
                        "path": "/delivery-management/employee-view",
                        "icon": "👤",
                        "order": 3,
                    },
                ],
            },

            # ------------------ USER MANAGEMENT ------------------
            {
                "name": "User Management",
                "key": "user_management",
                "path": "#",
                "icon": "🧑",
                "order": 6,
                "children": [
                    {
                        "name": "Add User",
                        "key": "user_add",
                        "path": "/add-user",
                        "icon": "➕",
                        "order": 1,
                    },
                    {
                        "name": "User Control",
                        "key": "user_control",
                        "path": "/user-control",
                        "icon": "🔐",
                        "order": 2,
                    },
                ],
            },

            # ------------------ MASTER ------------------
            {
                "name": "Master",
                "key": "master",
                "path": "#",
                "icon": "⚙️",
                "order": 7,
                "children": [
                    {
                        "name": "Department",
                        "key": "master_department",
                        "path": "/master/department",
                        "icon": "🏢",
                        "order": 1,
                    },
                    {
                        "name": "Vehicle Master",
                        "key": "master_vehicle",
                        "path": "/master/vehicle-master",
                        "icon": "🚗",
                        "order": 2,
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
        
        # Verify full menu structure
        self.stdout.write("\n🔍 VERIFYING MENU STRUCTURE:")
        self.stdout.write("-" * 110)

        top_level_keys = [
            ('hr', 'HR Management'),
            ('vehicle', 'Vehicle Management'),
            ('target_management', 'Target Management'),
            ('warehouse_management', 'Warehouse Management'),
            ('delivery_management', 'Delivery Management'),
            ('user_management', 'User Management'),
            ('master', 'Master'),
        ]

        for key, label in top_level_keys:
            try:
                item = MenuItem.objects.get(key=key)
                children = item.children.filter(is_active=True).order_by('order')
                child_count = children.count()
                if child_count:
                    self.stdout.write(self.style.SUCCESS(f"\n✅ {label} — {child_count} children:"))
                    for i, child in enumerate(children, 1):
                        self.stdout.write(f"   {i}. {child.name} ({child.key}) - {child.path}")
                        if child.children.exists():
                            for j, subchild in enumerate(child.children.filter(is_active=True).order_by('order'), 1):
                                self.stdout.write(f"      {i}.{j}. {subchild.name} ({subchild.key}) - {subchild.path}")
                else:
                    self.stdout.write(self.style.SUCCESS(f"\n✅ {label} — direct link: {item.path}"))
            except MenuItem.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ {label} not found!"))

        self.stdout.write("\n" + "=" * 110)
        self.stdout.write("\n💡 Next steps:")
        self.stdout.write("   1. Run: python manage.py seed_menus")
        self.stdout.write("   2. Assign menu permissions in User Control Panel")
        self.stdout.write("   3. Logout from application")
        self.stdout.write("   4. Clear browser cache: localStorage.clear() + sessionStorage.clear()")
        self.stdout.write("   5. Login again")
        self.stdout.write("\n📌 Menu sections seeded:")
        self.stdout.write("   1. HR Management       — Recruitment, Attendance Mgmt, Punch In/Out, HR Master, Leave Mgmt, Request, Payroll")
        self.stdout.write("   2. Vehicle Management  — Fuel Management, Travel, Challan")
        self.stdout.write("   3. Target Management   — My Targets, Sales, Call Targets, Master Data")
        self.stdout.write("   4. Warehouse Management — /under-construction (direct link)")
        self.stdout.write("   5. Delivery Management — List Deliveries, Create Delivery, Employee Delivery View")
        self.stdout.write("   6. User Management     — Add User, User Control")
        self.stdout.write("   7. Master              — Department, Vehicle Master")
        self.stdout.write("\n" + "=" * 110 + "\n")