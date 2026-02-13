# user_controll/management/commands/seed_menus.py
from django.core.management.base import BaseCommand
from user_controll.models import MenuItem


class Command(BaseCommand):
    help = 'Seed menu items with Delivery Management section'

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
                    {
                        "name": "Employee Management",
                        "key": "hr_employee",
                        "path": "/employee-management",
                        "icon": "👥",
                        "order": 4,
                    },
                    {
                        "name": "Attendance",
                        "key": "hr_attendance_main",
                        "path": "#",
                        "icon": "📊",
                        "order": 5,
                        "children": [
                            {
                                "name": "Attendance Management",
                                "key": "hr_attendance",
                                "path": "/attendance-management",
                                "icon": "📊",
                                "order": 1,
                            },
                            {
                                "name": "Punch In/Out",
                                "key": "hr_punchinpunchout",
                                "path": "/punch-in-out",
                                "icon": "⏰",
                                "order": 2,
                            },
                            {
                                "name": "Attendance Summary",
                                "key": "hr_attendance_summary",
                                "path": "/attendance-summary",
                                "icon": "📈",
                                "order": 3,
                            },
                        ],
                    },
                    {
                        "name": "Leave Management",
                        "key": "hr_leave_main",
                        "path": "#",
                        "icon": "🗓️",
                        "order": 6,
                        "children": [
                            {
                                "name": "Leave Management",
                                "key": "hr_leave_management",
                                "path": "/leave-management",
                                "icon": "🗓️",
                                "order": 1,
                            },
                            {
                                "name": "Request Leave",
                                "key": "hr_request_leave",
                                "path": "/leave-management/add",
                                "icon": "➕",
                                "order": 2,
                            },
                        ],
                    },
                    {
                        "name": "Certificates",
                        "key": "hr_certificates",
                        "path": "#",
                        "icon": "🎓",
                        "order": 7,
                        "children": [
                            {
                                "name": "Experience Certificate",
                                "key": "hr_experience",
                                "path": "/experience-certificate",
                                "icon": "🎓",
                                "order": 1,
                            },
                            {
                                "name": "Salary Certificate",
                                "key": "hr_salary",
                                "path": "/salary-certificate",
                                "icon": "💰",
                                "order": 2,
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
                        "name": "User Control Panel",
                        "key": "user_control",
                        "path": "/user-control",
                        "icon": "🔐",
                        "order": 1,
                    },
                    {
                        "name": "Add User",
                        "key": "user_add",
                        "path": "/add-user",
                        "icon": "➕",
                        "order": 2,
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
                        "name": "Payroll Processing",
                        "key": "payroll_processing",
                        "path": "/payroll",
                        "icon": "📋",
                        "order": 1,
                    },
                    {
                        "name": "Payslip",
                        "key": "payroll_payslip",
                        "path": "/payslip",
                        "icon": "📄",
                        "order": 2,
                    },
                ],
            },

            # ------------------ TARGET MANAGEMENT ------------------
            {
                "name": "Target Management",
                "key": "target_management",
                "path": "#",
                "icon": "🎯",
                "order": 4,
                "children": [
                    # NEW: Manager Dashboard (First item for managers)
                    {
                        "name": "Manager Dashboard",
                        "key": "target_dashboard",
                        "path": "/target/dashboard",
                        "icon": "📊",
                        "order": 1,
                    },
                    # NEW: My Targets (For regular employees)
                    {
                        "name": "My Targets",
                        "key": "target_my_targets",
                        "path": "#",
                        "icon": "🎯",
                        "order": 2,
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
                    # Route Targets
                    {
                        "name": "Route Targets",
                        "key": "target_route",
                        "path": "#",
                        "icon": "🗺️",
                        "order": 3,
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
                    # Call Targets
                    {
                        "name": "Call Targets",
                        "key": "target_call",
                        "path": "#",
                        "icon": "📞",
                        "order": 4,
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
                                "name": "Daily Activity",
                                "key": "target_call_daily_activity",
                                "path": "/target/call/daily-activity",
                                "icon": "📅",
                                "order": 3,
                            },
                            {
                                "name": "Call Performance",
                                "key": "target_call_performance",
                                "path": "/target/call/performance",
                                "icon": "📊",
                                "order": 4,
                            },
                        ],
                    },
                    # Master Data
                    {
                        "name": "Master Data",
                        "key": "target_master",
                        "path": "#",
                        "icon": "⚙️",
                        "order": 5,
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
                    # Reports (if needed)
                    {
                        "name": "Reports",
                        "key": "target_reports",
                        "path": "#",
                        "icon": "📈",
                        "order": 6,
                        "children": [
                            {
                                "name": "Route Performance",
                                "key": "target_report_route",
                                "path": "/target/route/performance",
                                "icon": "📊",
                                "order": 1,
                            },
                            {
                                "name": "Call Performance",
                                "key": "target_report_call",
                                "path": "/target/call/performance",
                                "icon": "📊",
                                "order": 2,
                            },
                            {
                                "name": "Employee Dashboard",
                                "key": "target_employee_dashboard",
                                "path": "/target/employee-dashboard",
                                "icon": "👤",
                                "order": 3,
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
                "order": 5,
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

            # ------------------ DELIVERY MANAGEMENT ------------------
            {
                "name": "Delivery Management",
                "key": "delivery_management",
                "path": "#",
                "icon": "🚚",
                "order": 6,
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
                        "name": "Today's Deliveries",
                        "key": "delivery_today",
                        "path": "/delivery-management/deliveries/today",
                        "icon": "📅",
                        "order": 3,
                    },
                    {
                        "name": "Upcoming Deliveries",
                        "key": "delivery_upcoming",
                        "path": "/delivery-management/deliveries/upcoming",
                        "icon": "🔜",
                        "order": 4,
                    },
                    {
                        "name": "Statistics",
                        "key": "delivery_statistics",
                        "path": "/delivery-management/deliveries/statistics",
                        "icon": "📊",
                        "order": 5,
                    },
                ],
            },

            # ------------------ MASTER DATA ------------------
            {
                "name": "Master Data",
                "key": "master",
                "path": "#",
                "icon": "⚙️",
                "order": 7,
                "children": [
                    {
                        "name": "Job Titles",
                        "key": "master_job_titles",
                        "path": "/master/job-titles",
                        "icon": "💼",
                        "order": 1,
                    },
                    {
                        "name": "Department",
                        "key": "master_department",
                        "path": "/master/department",
                        "icon": "🏢",
                        "order": 2,
                    },
                    {
                        "name": "Leave Types",
                        "key": "master_leave_types",
                        "path": "/master/leave-types",
                        "icon": "🗓️",
                        "order": 3,
                    },
                    {
                        "name": "Deductions",
                        "key": "master_deductions",
                        "path": "/master/deductions",
                        "icon": "💸",
                        "order": 4,
                    },
                    {
                        "name": "Allowances",
                        "key": "master_allowances",
                        "path": "/master/allowences",
                        "icon": "💵",
                        "order": 5,
                    },
                    {
                        "name": "WhatsApp Admin",
                        "key": "master_whatsapp_admin",
                        "path": "/master/whatsapp-admin",
                        "icon": "📱",
                        "order": 6,
                    },
                    {
                        "name": "Office Setup",
                        "key": "master_office_setup",
                        "path": "/master/office-setup",
                        "icon": "🏢",
                        "order": 7,
                    },
                    {
                        "name": "Vehicle Master",
                        "key": "master_vehicle",
                        "path": "/master/vehicle-master",
                        "icon": "🚗",
                        "order": 8,
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
        
        # Verify Delivery Management structure
        self.stdout.write("\n🔍 VERIFYING DELIVERY MANAGEMENT STRUCTURE:")
        self.stdout.write("-" * 110)
        
        try:
            delivery_mgmt = MenuItem.objects.get(key='delivery_management')
            children = delivery_mgmt.children.filter(is_active=True).order_by('order')
            self.stdout.write(self.style.SUCCESS(f"\n✅ Delivery Management found with {children.count()} children:"))
            for i, child in enumerate(children, 1):
                self.stdout.write(f"   {i}. {child.name} ({child.key}) - {child.path}")
                if child.children.exists():
                    for j, subchild in enumerate(child.children.filter(is_active=True).order_by('order'), 1):
                        self.stdout.write(f"      {i}.{j}. {subchild.name} ({subchild.key}) - {subchild.path}")
            
            self.stdout.write(self.style.SUCCESS("\n✅ Delivery Management menu structure verified!"))
            
            # Highlight new additions
            self.stdout.write("\n" + "=" * 110)
            self.stdout.write(self.style.SUCCESS("🆕 DELIVERY MANAGEMENT MENU ITEMS ADDED:"))
            self.stdout.write("-" * 110)
            self.stdout.write("   1. List Deliveries - /delivery-management/deliveries")
            self.stdout.write("   2. Create Delivery - /delivery-management/deliveries/new")
            self.stdout.write("   3. Today's Deliveries - /delivery-management/deliveries/today")
            self.stdout.write("   4. Upcoming Deliveries - /delivery-management/deliveries/upcoming")
            self.stdout.write("   5. Statistics - /delivery-management/deliveries/statistics")
            self.stdout.write("=" * 110)
                
        except MenuItem.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ Delivery Management menu not found!"))
        
        self.stdout.write("\n" + "=" * 110)
        self.stdout.write("\n💡 Next steps:")
        self.stdout.write("   1. Run: python manage.py seed_menus")
        self.stdout.write("   2. Assign menu permissions in User Control Panel")
        self.stdout.write("   3. Logout from application")
        self.stdout.write("   4. Clear browser cache: localStorage.clear() + sessionStorage.clear()")
        self.stdout.write("   5. Login again")
        self.stdout.write("   6. Check Delivery Management menu in sidebar!")
        self.stdout.write("\n📌 NOTE: Delivery Management features:")
        self.stdout.write("   - List Deliveries: View all deliveries with filtering")
        self.stdout.write("   - Create Delivery: Add new delivery with products and stops")
        self.stdout.write("   - Today's Deliveries: Quick view of today's scheduled deliveries")
        self.stdout.write("   - Upcoming Deliveries: See future scheduled deliveries")
        self.stdout.write("   - Statistics: Overview of delivery performance and metrics")
        self.stdout.write("\n" + "=" * 110 + "\n")