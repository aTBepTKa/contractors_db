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

        admins = User.objects.filter(is_superuser=True)

        for user in admins:
            user.groups.add(admin_group)

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
            f"Суперпользователи добавлены в группу Администратор: {admins.count()}"
        )