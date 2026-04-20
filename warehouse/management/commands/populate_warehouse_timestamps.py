from django.core.management.base import BaseCommand
from warehouse.models import WarehouseTask


class Command(BaseCommand):
    help = 'Populate start_datetime and completed_datetime for existing warehouse tasks'

    def handle(self, *args, **options):
        updated = 0
        
        for task in WarehouseTask.objects.all():
            changed = False
            
            # Set start_datetime from created_at if not already set
            if not task.start_datetime:
                task.start_datetime = task.created_at
                changed = True
                self.stdout.write(f"Task {task.id}: Set start_datetime to {task.created_at}")
            
            # Set completed_datetime for completed tasks
            if task.status == 'Completed' and not task.completed_datetime:
                task.completed_datetime = task.updated_at
                changed = True
                self.stdout.write(f"Task {task.id}: Set completed_datetime to {task.updated_at}")
            
            if changed:
                task.save(update_fields=['start_datetime', 'completed_datetime'])
                updated += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated} tasks with timestamps'
            )
        )
