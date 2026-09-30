from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create application user groups: Администратор and Пользователь"

    def handle(self, *args, **options):
        admin_group, admin_created = Group.objects.get_or_create(
            name="Администратор"
        )

        user_group, user_created = Group.objects.get_or_create(
            name="Пользователь"
        )

        User = get_user_model()

        admins = User.objects.filter(is_superuser=True) | User.objects.filter(is_staff=True)
        regular_users = User.objects.exclude(id__in=admins.values("id"))

        for user in admins:
            user.groups.add(admin_group)
            user.groups.remove(user_group)

        for user in regular_users:
            user.groups.add(user_group)
            user.groups.remove(admin_group)

        self.stdout.write(
            self.style.SUCCESS(
                "Группы пользователей проверены/созданы."
            )
        )

        if admin_created:
            self.stdout.write("Создана группа: Администратор")
        else:
            self.stdout.write("Группа уже существовала: Администратор")

        if user_created:
            self.stdout.write("Создана группа: Пользователь")
        else:
            self.stdout.write("Группа уже существовала: Пользователь")

        self.stdout.write(
            f"Администраторы добавлены в группу Администратор: {admins.count()}"
        )
        self.stdout.write(
            f"Обычные пользователи добавлены в группу Пользователь: {regular_users.count()}"
        )
