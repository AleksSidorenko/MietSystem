# users/management/commands/assign_groups_by_role.py
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = "Sync groups to match user.role"

    def handle(self, *args, **options):
        self.stdout.write("🔄 Syncing user groups with their role...")

        for user in User.objects.exclude(is_superuser=True):
            role_group_name = user.role.capitalize()

            try:
                group = Group.objects.get(name=role_group_name)
                user.groups.clear()
                user.groups.add(group)
                self.stdout.write(f"✅ {user.email} -> {group.name}")
            except Group.DoesNotExist:
                self.stdout.write(
                    f"⚠️ Group '{role_group_name}' not found for user {user.email}"
                )

        self.stdout.write("✅ Group sync completed.")
