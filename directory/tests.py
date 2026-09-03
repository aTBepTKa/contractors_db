from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import (
    Executor,
    ExecutorStatus,
    ObjectType,
    Project,
    ProjectSelection,
    SelectionStatus,
    Specialty,
)


class ProjectSelectionAutosaveTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="test-password",
        )
        executor_status = ExecutorStatus.objects.create(name="Активный")
        self.executor = Executor.objects.create(
            last_name="Иванов",
            first_name="Иван",
            status=executor_status,
        )
        self.specialty = Specialty.objects.create(code="АР", name="Архитектура")
        self.initial_status = SelectionStatus.objects.create(name="Новый")
        self.ready_status = SelectionStatus.objects.create(name="Готов")
        object_type = ObjectType.objects.create(name="Общественное здание")
        self.project = Project.objects.create(
            name="Тестовый проект",
            object_type=object_type,
        )
        self.selection = ProjectSelection.objects.create(
            project=self.project,
            specialty=self.specialty,
            executor=self.executor,
            status=self.initial_status,
            offer_amount=100_000,
            comment="Исходный комментарий",
        )
        self.url = reverse(
            "update_project_selection",
            kwargs={"selection_id": self.selection.id},
        )

    def autosave(self, field, value):
        return self.client.post(
            self.url,
            {"autosave": "1", "field": field, "value": value},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_login_is_required(self):
        response = self.autosave("comment", "Новое значение")

        self.assertEqual(response.status_code, 302)
        self.selection.refresh_from_db()
        self.assertEqual(self.selection.comment, "Исходный комментарий")

    def test_status_is_saved(self):
        self.client.force_login(self.user)

        response = self.autosave("status_id", str(self.ready_status.id))

        self.assertEqual(response.status_code, 200)
        self.selection.refresh_from_db()
        self.assertEqual(self.selection.status, self.ready_status)
        self.assertEqual(response.json()["status_css_class"], "selection-status-ready")

    def test_offer_amount_is_saved_and_formatted(self):
        self.client.force_login(self.user)

        response = self.autosave("offer_amount", "1 250 000")

        self.assertEqual(response.status_code, 200)
        self.selection.refresh_from_db()
        self.assertEqual(self.selection.offer_amount, 1_250_000)
        self.assertEqual(response.json()["display_value"], "1 250 000")

    def test_empty_offer_amount_is_saved_as_null(self):
        self.client.force_login(self.user)

        response = self.autosave("offer_amount", "")

        self.assertEqual(response.status_code, 200)
        self.selection.refresh_from_db()
        self.assertIsNone(self.selection.offer_amount)
        self.assertEqual(response.json()["display_value"], "")

    def test_invalid_offer_amount_does_not_replace_saved_value(self):
        self.client.force_login(self.user)

        response = self.autosave("offer_amount", "12,5 тыс.")

        self.assertEqual(response.status_code, 400)
        self.selection.refresh_from_db()
        self.assertEqual(self.selection.offer_amount, 100_000)
        self.assertIn("целым числом", response.json()["error"])

    def test_comment_is_saved(self):
        self.client.force_login(self.user)

        response = self.autosave("comment", "  Новый комментарий  ")

        self.assertEqual(response.status_code, 200)
        self.selection.refresh_from_db()
        self.assertEqual(self.selection.comment, "Новый комментарий")

    def test_unknown_field_is_rejected(self):
        self.client.force_login(self.user)

        response = self.autosave("project_id", "999")

        self.assertEqual(response.status_code, 400)
        self.selection.refresh_from_db()
        self.assertEqual(self.selection.project, self.project)
