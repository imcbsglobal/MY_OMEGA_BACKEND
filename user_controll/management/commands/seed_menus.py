from django.core.management.base import BaseCommand
from user_controll.models import MenuItem


class Command(BaseCommand):
    help = 'Seed menu items matching your HR System structure'

    def handle(self, *args, **options):
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
                        "name": "Interview Management",
                        "key": "hr_interview",
                        "path": "/hr/interview-management",
                        "icon": "👤",
                        "order": 1,
                    },
                    {
                        "name": "Offer Letter",
                        "key": "hr_offer_letter",
                        "path": "/hr/offer-letter",
                        "icon": "📄",
                        "order": 2,
                    },
                    {
                        "name": "Employee Management",
                        "key": "hr_employee",
                        "path": "/hr/employee-management",
                        "icon": "👥",
                        "order": 3,
                    },
                    {
                        "name": "Attendance Management",
                        "key": "hr_attendance",
                        "path": "/hr/attendance",
                        "icon": "📊",
                        "order": 4,
                    },
                    {
                        "name": "Punch In / Punch Out",
                        "key": "hr_punch",
                        "path": "/hr/PunchinPunchout",
                        "icon": "FaUserClock",
                        "order": 5,
                    },
                    {
                        "name": "Leave Management",
                        "key": "hr_leave",
                        "path": "/hr/leave-management",
                        "icon": "FaCalendarCheck",
                        "order": 6,
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
                        "name": "User List",
                        "key": "user_list",
                        "path": "/user/list",
                        "icon": "FaUsersCog",
                        "order": 1,
                    },
                    {
                        "name": "User Control",
                        "key": "user_control",
                        "path": "/admin/user-control",
                        "icon": "🔒",
                        "order": 2,
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