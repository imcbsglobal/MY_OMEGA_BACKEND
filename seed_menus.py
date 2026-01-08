from django.core.management.base import BaseCommand
from user_controll.models import MenuItem


class Command(BaseCommand):
    help = 'Seed menu items matching your HR System structure'

    def handle(self, *args, **options):
        # First, let's clear old menu items to avoid conflicts
        self.stdout.write("Clearing existing menu items...")
        MenuItem.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("✓ Cleared existing menu items"))
        
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
                    {
                        "name": "Employee Management",
                        "key": "hr_employee",
                        "path": "/employee-management",
                        "icon": "👥",
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
                        "name": "Salary Certificate",
                        "key": "hr_salary",
                        "path": "/salary-certificate",
                        "icon": "💰",
                        "order": 6,
                    },
                    {
                        "name": "Attendance",
                        "key": "hr_attendance",
                        "path": "#",
                        "icon": "📊",
                        "order": 7,
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
                        "name": "Leave Management",
                        "key": "hr_leave",
                        "path": "#",
                        "icon": "🗓️",
                        "order": 8,
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
                        "order": 9,
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