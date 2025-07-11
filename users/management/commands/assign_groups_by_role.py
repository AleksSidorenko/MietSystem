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


# from django.core.management.base import BaseCommand
# from django.contrib.auth.models import Group
# from users.models import User
#
# class Command(BaseCommand):
#     help = 'Assign users to groups based on their role field'
#
#     def handle(self, *args, **options):
#         self.stdout.write('Starting to assign groups based on roles...')
#         users = User.objects.all()
#         for user in users:
#             if user.is_superuser:
#                 continue  # пропускаем суперпользователей
#             # Очищаем группы
#             user.groups.clear()
#             try:
#                 # Ищем группу с именем роли с первой заглавной буквой
#                 group_name = user.role.capitalize()
#                 group = Group.objects.get(name=group_name)
#                 user.groups.add(group)
#                 self.stdout.write(f'User {user.email} assigned to group {group_name}')
#             except Group.DoesNotExist:
#                 self.stderr.write(f'Group "{group_name}" does not exist. Skipping user {user.email}')
#         self.stdout.write('Group assignment completed.')
