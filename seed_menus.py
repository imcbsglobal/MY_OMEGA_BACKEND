from django.core.management.base import BaseCommand
from user_controll.models import MenuItem


class Command(BaseCommand):
    help = 'Seed menu items matching your HR System structure'

    def handle(self, *args, **options):
        # First, let's clear old menu items to avoid conflicts
        self.stdout.write("\n" + "="*60)
        self.stdout.write("Seeding menus safely (No deletion)...")
        self.stdout.write("="*60 + "\n")
        
        # Define your exact menu structure
        menus = [
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
                        "icon": "🧑‍💼",
                        "order": 1,
                        "children": [
                            {
                                "name": "CV Management",
                                "key": "hr_cv",
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
                        ]
                    },
                    {
                        "name": "Employee Management",
                        "key": "hr_employee",
                        "path": "/employee-management",
                        "icon": "👥",
                        "order": 2,
                    },
                    {
                        "name": "Experience Certificate",
                        "key": "hr_experience",
                        "path": "/experience-certificate",
                        "icon": "🎓",
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
                        "name": "Attendance",
                        "key": "hr_attendance",
                        "path": "#",
                        "icon": "📊",
                        "order": 5,
                        "children": [
                            {
                                "name": "Attendance Management",
                                "key": "attendance_mgmt",
                                "path": "/attendance-management",
                                "icon": "📊",
                                "order": 1,
                            },
                            {
                                "name": "Attendance Summary",
                                "key": "attendance_summary",
                                "path": "/attendance-summary",
                                "icon": "📈",
                                "order": 2,
                            },
                            {
                                "name": "Punch In / Punch Out",
                                "key": "punch_in_out",
                                "path": "/punch-in-out",
                                "icon": "⏰",
                                "order": 3,
                            },
                        ]
                    },
                    {
                        "name": "HR Master",
                        "key": "hr_master",
                        "path": "#",
                        "icon": "⚙️",
                        "order": 6,
                        "children": [
                            {
                                "name": "Job Titles",
                                "key": "job_titles",
                                "path": "/master/job-titles",
                                "icon": "💼",
                                "order": 1,
                            },
                            {
                                "name": "Leave Types",
                                "key": "master_leave_types",
                                "path": "/master/leave-types",
                                "icon": "🗂️",
                                "order": 2,
                            },
                            {
                                "name": "Deductions",
                                "key": "master_deductions",
                                "path": "/master/deductions",
                                "icon": "➖",
                                "order": 3,
                            },
                            {
                                "name": "Allowences",
                                "key": "master_allowences",
                                "path": "/master/allowences",
                                "icon": "➕",
                                "order": 4,
                            },
                            {
                                "name": "WhatsApp Admin",
                                "key": "master_whatsapp_admin",
                                "path": "/master/whatsapp-admin",
                                "icon": "🟢",
                                "order": 5,
                            },
                            {
                                "name": "Office Setup",
                                "key": "hr_office_setup",
                                "path": "/hr/master/office-setup",
                                "icon": "🏢",
                                "order": 6,
                            },
                        ]
                    },
                    {
                        "name": "Leave Management",
                        "key": "hr_leave",
                        "path": "#",
                        "icon": "🗓️",
                        "order": 7,
                        "children": [
                            {
                                "name": "Leave Management",
                                "key": "leave_mgmt",
                                "path": "/leave-management",
                                "icon": "🗓️",
                                "order": 1,
                            },
                            
                            {
                                "name": "Leave List",
                                "key": "leave_list",
                                "path": "/leave-management/leave-list",
                                "icon": "📋",
                                "order": 3,
                            },
                            {
                                "name": "Early List",
                                "key": "early_list",
                                "path": "/leave-management/early-list",
                                "icon": "🌅",
                                "order": 4,
                            },
                            {
                                "name": "Late List",
                                "key": "late_list",
                                "path": "/leave-management/late-list",
                                "icon": "🌆",
                                "order": 5,
                            },
                            
                        ]
                    },
                    {
                        "name": "Requests",
                        "key": "hr_requests",
                        "path": "#",
                        "icon": "📝",
                        "order": 8,
                        "children": [
                            {
                                "name": "Leave Request",
                                "key": "leave_request",
                                "path": "/hr/request/leave",
                                "icon": "🗓️",
                                "order": 1,
                            },
                            {
                                "name": "Late Request",
                                "key": "late_request",
                                "path": "/hr/request/late",
                                "icon": "⏰",
                                "order": 2,
                            },
                            {
                                "name": "Early Request",
                                "key": "early_request",
                                "path": "/hr/request/early",
                                "icon": "🌅",
                                "order": 3,
                            },
                        ]
                    },
                    {
                        "name": "Payroll",
                        "key": "payroll",
                        "path": "#",
                        "icon": "💳",
                        "order": 9,
                        "children": [
                            { "name": "Payroll", "key": "payroll_home", "path": "/payroll", "icon": "💳", "order": 1 },
                            { "name": "Payslip", "key": "payslip", "path": "/payslip", "icon": "📄", "order": 2 },
                        ]
                    },
                ]
            },
            {
                "name": "User Management",
                "key": "user_management",
                "path": "#",
                "icon": "🧑",
                "order": 2,
                "children": [
                    {
                        "name": "Add User",
                        "key": "add_user",
                        "path": "/add-user",
                        "icon": "FaUserCog",
                        "order": 1,
                    },
                    {
                        "name": "User Control",
                        "key": "user_control",
                        "path": "/user-control",
                        "icon": "🔒",
                        "order": 2,
                    },
                        {
                            "name": "Marketing",
                            "key": "user_marketing",
                            "path": "#",
                            "icon": "📢",
                            "order": 3,
                            "children": [
                                {
                                    "name": "Marketing Assign",
                                    "key": "user_marketing_assign",
                                    "path": "/user/marketing/assign",
                                    "icon": "📢",
                                    "order": 1,
                                },
                                {
                                    "name": "Marketing View",
                                    "key": "user_marketing_view",
                                    "path": "/user/marketing/view",
                                    "icon": "📢",
                                    "order": 2,
                                },
                            ]
                        },
                ]
            },
            {
                "name": "Master Data",
                "key": "master",
                "path": "#",
                "icon": "⚙️",
                "order": 3,
                "children": [
                    {
                        "name": "Job Titles",
                        "key": "job_titles",
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
                        "name": "Vehicle Master",
                        "key": "master_vehicle_master",
                        "path": "/master/vehicle-master",
                        "icon": "🚗",
                        "order": 3,
                    },
                ]
            },
            {
                "name": "Delivery Management",
                "key": "delivery_management",
                "path": "#",
                "icon": "🚚",
                "order": 4,
                "children": [
                    {
                        "name": "Deliveries",
                        "key": "deliveries_list",
                        "path": "/delivery-management/deliveries",
                        "icon": "📦",
                        "order": 1,
                    },
                    {
                        "name": "New Delivery",
                        "key": "deliveries_new",
                        "path": "/delivery-management/deliveries/new",
                        "icon": "➕",
                        "order": 2,
                    },
                    {
                        "name": "Employee View",
                        "key": "delivery_employee_view",
                        "path": "/delivery-management/employee-view",
                        "icon": "👷",
                        "order": 3,
                    },
                ]
            },
            {
                "name": "Vehicle Management",
                "key": "vehicle_management",
                "path": "#",
                "icon": "🚗",
                "order": 5,
                "children": [
                    { "name": "Fuel Management", "key": "vehicle_fuel", "path": "/vehicle/fuel-management", "icon": "⛽", "order": 1 },
                    { "name": "Travel", "key": "vehicle_travel", "path": "/vehicle/travel", "icon": "🛣️", "order": 2 },
                    { "name": "Challan", "key": "vehicle_challan", "path": "/vehicle/challan", "icon": "🧾", "order": 3 },
                ]
            },
            {
                "name": "Target Management",
                "key": "target_management",
                "path": "#",
                "icon": "🎯",
                "order": 6,
                "children": [
                    {
                        "name": "My Targets",
                        "key": "target_my_targets",
                        "path": "#",
                        "icon": "🎯",
                        "order": 1,
                        "children": [
                            { "name": "View My Targets", "key": "target_my_targets_view", "path": "/target/my-targets", "icon": "👤", "order": 1 },
                        ]
                    },
                        {
                            "name": "Marketing",
                            "key": "target_marketing",
                            "path": "#",
                            "icon": "📢",
                            "order": 1.5,
                            "children": [
                                { "name": "Marketing Assign", "key": "target_marketing_assign", "path": "/target/marketing/assign", "icon": "📢", "order": 1 },
                                { "name": "Marketing View", "key": "target_marketing_view", "path": "/target/call/marketing/view", "icon": "📢", "order": 2 },
                            ]
                        },
                    {
                        "name": "Marketing Targets",
                        "key": "target_marketing_targets",
                        "path": "/target/call/marketing",
                        "icon": "📢",
                        "order": 2,
                    },
                    {
                        "name": "Route Targets",
                        "key": "target_route_targets",
                        "path": "#",
                        "icon": "🗺️",
                        "order": 3,
                        "children": [
                            { "name": "Assign Route Target", "key": "target_route_assign", "path": "/target/route/assign", "icon": "🗺️", "order": 1 },
                            { "name": "Route Target List", "key": "target_route_list", "path": "/target/route/list", "icon": "📋", "order": 2 },
                            { "name": "Route Performance", "key": "target_route_performance", "path": "/target/route/performance", "icon": "📈", "order": 3 },
                        ]
                    },
                    {
                        "name": "Call Targets",
                        "key": "target_call_targets",
                        "path": "#",
                        "icon": "📞",
                        "order": 4,
                        "children": [
                            { "name": "Assign Call Target", "key": "target_call_assign", "path": "/target/call/assign", "icon": "📞", "order": 1 },
                            { "name": "Call Target List", "key": "target_call_list", "path": "/target/call/list", "icon": "📋", "order": 2 },
                            { "name": "Call Performance", "key": "target_call_performance", "path": "/target/call/performance", "icon": "📈", "order": 3 },
                        ]
                    },
                    {
                        "name": "Master Data",
                        "key": "target_master_data",
                        "path": "#",
                        "icon": "⚙️",
                        "order": 5,
                        "children": [
                            { "name": "Routes", "key": "target_master_routes", "path": "/target/master/routes", "icon": "🗺️", "order": 1 },
                            { "name": "Products", "key": "target_master_products", "path": "/target/master/products", "icon": "📦", "order": 2 },
                        ]
                    },
                    {
                        "name": "Manager Dashboard",
                        "key": "target_manager_dashboard",
                        "path": "/target/dashboard",
                        "icon": "📊",
                        "order": 6,
                    },
                    {
                        "name": "Comparative Performance",
                        "key": "target_comparative_performance",
                        "path": "/target/performance/comparative",
                        "icon": "📈",
                        "order": 7,
                    },
                ]
            },
            {
                "name": "Warehouse Management",
                "key": "warehouse_management",
                "path": "#",
                "icon": "🏭",
                "order": 7,
                "children": [
                    { "name": "Warehouses", "key": "warehouse_list", "path": "/warehouse/warehouses", "icon": "🏬", "order": 1 },
                    { "name": "Stock", "key": "warehouse_stock", "path": "/warehouse/stock", "icon": "📦", "order": 2 },
                    { "name": "Stock Transfer", "key": "warehouse_stock_transfer", "path": "/warehouse/stock-transfer", "icon": "🔁", "order": 3 },
                    { "name": "Assign Work", "key": "warehouse_assign", "path": "/warehouse/assign", "icon": "📋", "order": 4 },
                    { "name": "Task Monitor", "key": "warehouse_admin", "path": "/warehouse/admin", "icon": "📊", "order": 5 },
                    { "name": "My Warehouse Tasks", "key": "warehouse_mytasks", "path": "/warehouse/mytasks", "icon": "📦", "order": 6 },
                ]
            },
                {
                    "name": "Frontend Navbar",
                    "key": "frontend_navbar",
                    "path": "#",
                    "icon": "🖥️",
                    "order": 8,
                    "children": [
                        {"name": "HR Management", "key": "frontend_hr_management", "path": "/cv-management", "icon": "👥", "order": 1},
                        {"name": "Interview Management", "key": "frontend_interview_management", "path": "/interview-management", "icon": "👤", "order": 2},
                        {"name": "Offer Letter", "key": "frontend_offer_letter", "path": "/offer-letter", "icon": "📄", "order": 3},
                        {"name": "Employee Management", "key": "frontend_employee_management", "path": "/employee-management", "icon": "👥", "order": 4},
                        {"name": "Attendance Management", "key": "frontend_attendance_management", "path": "/attendance-management", "icon": "📊", "order": 5},
                        {"name": "Punch In / Punch Out", "key": "frontend_punch_in_out", "path": "/punch-in-out", "icon": "⏰", "order": 6},
                        {"name": "Leave Management", "key": "frontend_leave_management", "path": "/leave-management", "icon": "🗓️", "order": 7},
                        {"name": "Experience Certificate", "key": "frontend_experience_certificate", "path": "/experience-certificate", "icon": "🎓", "order": 8},
                        {"name": "Salary Certificate", "key": "frontend_salary_certificate", "path": "/salary-certificate", "icon": "💰", "order": 9},
                        {"name": "Vehicle Management", "key": "frontend_vehicle_management", "path": "/company-vehicle", "icon": "🚗", "order": 10},
                        {"name": "Target Management", "key": "frontend_target_management", "path": "/target/my-targets", "icon": "🎯", "order": 11},
                        {"name": "Warehouse Management", "key": "frontend_warehouse_management", "path": "/warehouse-list", "icon": "🏭", "order": 12},
                        {"name": "Delivery Management", "key": "frontend_delivery_management", "path": "/delivery-status", "icon": "🚚", "order": 13},
                        {"name": "User Management", "key": "frontend_user_management", "path": "/add-user", "icon": "🧑", "order": 14},
                        {"name": "Master", "key": "frontend_master", "path": "/master-data", "icon": "⚙️", "order": 15},
                    ]
                },
        ]

        created_count = 0
        updated_count = 0
        
        def create_or_update_menu(menu_data, parent=None):
            nonlocal created_count, updated_count
            
            # Try to get existing menu by key
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
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Created: {menu_data['name']} ({menu_data['key']})")
                )
            else:
                # Update existing menu
                menu.name = menu_data["name"]
                menu.path = menu_data.get("path", "")
                menu.icon = menu_data.get("icon", "")
                menu.parent = parent
                menu.order = menu_data.get("order", 0)
                menu.is_active = True
                menu.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"⚠ Updated: {menu_data['name']} ({menu_data['key']})")
                )
            
            # Create/update children recursively
            for child_data in menu_data.get("children", []):
                create_or_update_menu(child_data, parent=menu)
        
        # Create/update all menus
        self.stdout.write("\n" + "="*60)
        self.stdout.write("Starting menu seed process...")
        self.stdout.write("="*60 + "\n")
        
        for menu_data in menus:
            create_or_update_menu(menu_data)
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write(
            self.style.SUCCESS(f"✅ Process complete!")
        )
        self.stdout.write(
            self.style.SUCCESS(f"   - Created: {created_count} new items")
        )
        self.stdout.write(
            self.style.SUCCESS(f"   - Updated: {updated_count} existing items")
        )
        self.stdout.write("="*60 + "\n")
        