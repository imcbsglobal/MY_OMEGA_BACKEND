from django.core.management.base import BaseCommand
from user_controll.models import ApprovalCategory


class Command(BaseCommand):
    help = 'Seed approval categories for HR system'

    def handle(self, *args, **options):
        categories = [
            {
                "name": "Attendance Approval",
                "key": "attendance_approval",
                "description": "Approve or reject attendance regularization requests",
                "order": 1
            },
            {
                "name": "Leave Approval",
                "key": "leave_approval",
                "description": "Approve or reject employee leave requests",
                "order": 2
            },
            {
                "name": "Offer Letter Approval",
                "key": "offer_letter_approval",
                "description": "Approve or reject offer letter generation",
                "order": 3
            },
            {
                "name": "Interview Approval",
                "key": "interview_approval",
                "description": "Approve or reject interview scheduling",
                "order": 4
            },
        ]

        created_count = 0
        updated_count = 0

        self.stdout.write("\n" + "="*60)
        self.stdout.write("Seeding Approval Categories...")
        self.stdout.write("="*60 + "\n")

        for cat_data in categories:
            category, created = ApprovalCategory.objects.get_or_create(
                key=cat_data["key"],
                defaults={
                    "name": cat_data["name"],
                    "description": cat_data["description"],
                    "order": cat_data["order"],
                    "is_active": True
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Created: {cat_data['name']}")
                )
            else:
                category.name = cat_data["name"]
                category.description = cat_data["description"]
                category.order = cat_data["order"]
                category.is_active = True
                category.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"⚠ Updated: {cat_data['name']}")
                )

        self.stdout.write("\n" + "="*60)
        self.stdout.write(
            self.style.SUCCESS(f"✅ Process complete!")
        )
        self.stdout.write(
            self.style.SUCCESS(f"   - Created: {created_count} new categories")
        )
        self.stdout.write(
            self.style.SUCCESS(f"   - Updated: {updated_count} existing categories")
        )
        self.stdout.write("="*60 + "\n")