from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from user_controll.models import MenuItem, UserMenuAccess


class Command(BaseCommand):
    help = "Grant Marketing Targets access (view/edit/delete) to specified users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-ids",
            nargs="*",
            type=int,
            help="Space separated user IDs to grant access to",
        )
        parser.add_argument(
            "--emails",
            nargs="*",
            type=str,
            help="Space separated user emails to grant access to",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Grant access to all users",
        )
        parser.add_argument(
            "--view",
            action="store_true",
            help="Grant view permission (default if no permission flags given)",
        )
        parser.add_argument(
            "--edit",
            action="store_true",
            help="Grant edit permission",
        )
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Grant delete permission",
        )

    def handle(self, *args, **options):
        User = get_user_model()

        user_ids = options.get("user_ids") or []
        emails = options.get("emails") or []
        give_all = options.get("all")

        # Determine permission flags
        can_view = options.get("view")
        can_edit = options.get("edit")
        can_delete = options.get("delete")

        # If no specific permission flags provided, default to view
        if not any([can_view, can_edit, can_delete]):
            can_view = True

        # Find the MenuItem for Marketing Targets by key
        menu_key = "target_marketing_targets"
        menu_item = MenuItem.objects.filter(key=menu_key).first()
        if not menu_item:
            self.stdout.write(self.style.ERROR(f"MenuItem with key '{menu_key}' not found. Run seed_menus or create it first."))
            return
        if not menu_item.is_active:
            self.stdout.write(self.style.ERROR(f"MenuItem '{menu_item.name}' (id={menu_item.id}) is not active. Activate it in admin or seed_menus."))
            return

        # Build user queryset
        qs = User.objects.none()
        if give_all:
            qs = User.objects.all()
        else:
            pks = list(user_ids)
            if emails:
                users_by_email = list(User.objects.filter(email__in=emails))
                pks += [u.pk for u in users_by_email]
            if pks:
                qs = User.objects.filter(pk__in=pks)

        if qs.count() == 0:
            self.stdout.write(self.style.WARNING("No users matched (use --user-ids, --emails or --all)."))
            return

        created = 0
        updated = 0
        for user in qs:
            access, was_created = UserMenuAccess.objects.get_or_create(user=user, menu_item=menu_item)
            changed = False
            if access.can_view != bool(can_view):
                access.can_view = bool(can_view); changed = True
            if access.can_edit != bool(can_edit):
                access.can_edit = bool(can_edit); changed = True
            if access.can_delete != bool(can_delete):
                access.can_delete = bool(can_delete); changed = True
            if was_created:
                created += 1
                access.save()
            else:
                if changed:
                    access.save()
                    updated += 1

            # Ensure ancestor parents have at least view permission so menus are visible
            parent = menu_item.parent
            while parent:
                pa, pcreated = UserMenuAccess.objects.get_or_create(user=user, menu_item=parent)
                if not pa.can_view:
                    pa.can_view = True
                    pa.save()
                parent = parent.parent

        self.stdout.write(self.style.SUCCESS(f"Processed {qs.count()} users: created={created}, updated={updated}"))
        self.stdout.write(self.style.SUCCESS("Done."))
