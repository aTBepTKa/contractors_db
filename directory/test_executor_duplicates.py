from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from .models import Executor, ExecutorStatus


class ExecutorDuplicateTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="duplicate-tester")
        self.status = ExecutorStatus.objects.create(name="Активный")
        self.executor = Executor.objects.create(last_name="Иванов", first_name="Иван", status=self.status,
                                                phone="+79990000000", email="test@example.com")
        self.url = reverse("executor_duplicates")

    def test_login_required(self):
        self.assertEqual(self.client.get(self.url, {"last_name": "Иванов"}).status_code, 302)

    def test_executor_admin_button_permissions(self):
        self.client.force_login(self.user)
        url = reverse("executor_detail", args=[self.executor.pk])
        self.assertNotContains(self.client.get(url), "Открыть в админке")
        self.user.is_staff = True
        self.user.save()
        self.assertContains(self.client.get(url), "Открыть в админке")
        self.user.groups.add(Group.objects.get(name="Только просмотр"))
        self.assertNotContains(self.client.get(url), "Открыть в админке")
        self.user.is_superuser = True
        self.user.save()
        self.assertContains(self.client.get(url), "Открыть в админке")

    def test_matches_exact_surname_ignoring_case_and_spaces(self):
        self.client.force_login(self.user)
        matches = self.client.get(self.url, {"last_name": " иВАНОВ "}).json()["matches"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["id"], self.executor.pk)
        self.assertEqual(matches[0]["email"], "test@example.com")
        self.assertEqual(matches[0]["phone"], "+79990000000")
        for surname in ("", "Иван", "Петров"):
            self.assertEqual(self.client.get(self.url, {"last_name": surname}).json()["matches"], [])

    def test_list_status_control_hidden_for_read_only(self):
        self.client.force_login(self.user)
        self.assertContains(self.client.get(reverse("executor_list")), 'class="list-status-form"')
        self.user.groups.add(Group.objects.get(name="Только просмотр"))
        self.assertNotContains(self.client.get(reverse("executor_list")), 'class="list-status-form"')
        self.assertEqual(self.client.post(reverse("update_executor_status", args=[self.executor.pk]),
                                         {"status_id": self.status.pk}).status_code, 403)
