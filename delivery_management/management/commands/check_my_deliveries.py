from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Check deliveries assigned to a given user (by email) or first non-staff user'

    def add_arguments(self, parser):
        parser.add_argument('--email', dest='email', help='Email of the user to inspect')

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        from delivery_management.models import Delivery

        User = get_user_model()
        email = options.get('email')
        if email:
            user = User.objects.filter(email__iexact=email).first()
            if not user:
                self.stdout.write(self.style.ERROR(f'No user found with email {email}'))
                return
        else:
            user = User.objects.filter(is_active=True).exclude(is_staff=True).first()
            if not user:
                self.stdout.write(self.style.WARNING('No non-staff active user found'))
                return

        qs = Delivery.objects.filter(assigned_to=user)
        self.stdout.write(f'Testing as user: {getattr(user, "email", str(user))}')
        self.stdout.write(f'Assigned deliveries count: {qs.count()}')
        for d in qs[:100]:
            self.stdout.write(f'- id={d.id} number={d.delivery_number} status={d.status} date={d.scheduled_date}')
