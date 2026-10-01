from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import (
    Executor,
    ExecutorStatus,
    ObjectType,
    Project,
    ProjectSelection,
    ProjectSpecialtyNeed,
    SelectionStatus,
    Software,
    Specialty,
)


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="login-tester",
            password="test-password",
        )

    def test_login_page_is_available(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Вход в систему")

    def test_login_returns_user_to_requested_page(self):
        response = self.client.post(
            reverse("login") + "?next=/",
            {"username": "login-tester", "password": "test-password", "next": "/"},
        )

        self.assertRedirects(response, "/", fetch_redirect_response=False)


class ReadOnlyAccessTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import Group
        self.user = get_user_model().objects.create_user(username="viewer")
        self.user.groups.add(Group.objects.get_or_create(name="Только просмотр")[0])
        self.client.force_login(self.user)

    def test_lists_are_available(self):
        for url in ("/", "/executors/", "/projects/"):
            self.assertContains(self.client.get(url), "Только просмотр")

    def test_all_directory_mutations_are_forbidden(self):
        from .urls import urlpatterns
        for pattern in urlpatterns:
            kwargs = {name: 999999 for name in pattern.pattern.converters}
            url = reverse(pattern.name, kwargs=kwargs)
            for method in ("post", "put", "patch", "delete"):
                with self.subTest(url=url, method=method):
                    self.assertEqual(getattr(self.client, method)(url).status_code, 403)

    def test_edit_pages_and_admin_are_forbidden_even_for_staff(self):
        self.user.is_staff = True
        self.user.save()
        for url in ("/executors/add/", "/projects/add/", "/executors/1/edit/", "/projects/1/edit/", "/admin/"):
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_logout_still_works(self):
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)

    def test_superuser_keeps_access(self):
        self.user.is_superuser = True
        self.user.save()
        self.assertEqual(self.client.get("/projects/add/").status_code, 200)


class HomeAdminAccessTests(TestCase):
    def test_regular_user_has_no_admin_links_or_admin_access(self):
        user = get_user_model().objects.create_user(username="regular")
        self.client.force_login(user)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'href="/admin/"')
        self.assertRedirects(
            self.client.get("/admin/"),
            "/admin/login/?next=/admin/",
            fetch_redirect_response=False,
        )

    def test_admin_users_see_admin_tile(self):
        for flag in ("is_staff", "is_superuser"):
            with self.subTest(flag=flag):
                user = get_user_model().objects.create_user(username=flag, **{flag: True})
                self.client.force_login(user)
                self.assertContains(self.client.get("/"), '<div class="tile-title">Админка</div>')


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

    def test_approved_status_is_saved_and_closes_section(self):
        from .views import get_need_status
        self.client.force_login(self.user)
        approved = SelectionStatus.objects.get(name="Утвержден")
        ProjectSpecialtyNeed.objects.create(project=self.project, specialty=self.specialty)
        response = self.autosave("status_id", str(approved.id))
        self.assertEqual(response.status_code, 200)
        self.selection.refresh_from_db()
        self.assertEqual(self.selection.status, approved)
        self.assertEqual(get_need_status([self.selection])["label"], "Закрыт")
        page = self.client.get(reverse("project_detail", kwargs={"project_id": self.project.id}))
        self.assertEqual(page.context["selection_status_counters"]["Утвержден"], 1)
        self.assertContains(page, "Утвержден")
        self.assertEqual(response.json()["section_status"]["label"], "Закрыт")
        self.assertEqual(response.json()["approved_count"], 1)
        response = self.autosave("status_id", str(self.ready_status.id))
        self.assertEqual(response.json()["section_status"]["label"], "В работе")
        self.assertEqual(response.json()["approved_count"], 0)

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

    def test_deleting_need_removes_project_selections_for_that_specialty(self):
        self.client.force_login(self.user)
        need = ProjectSpecialtyNeed.objects.create(
            project=self.project,
            specialty=self.specialty,
            created_by=self.user,
        )
        other_specialty = Specialty.objects.create(code="КР", name="Конструкции")
        other_selection = ProjectSelection.objects.create(
            project=self.project,
            specialty=other_specialty,
            executor=self.executor,
            status=self.initial_status,
        )

        response = self.client.post(reverse("delete_project_specialty_need", kwargs={"need_id": need.id}))

        self.assertRedirects(response, reverse("project_detail", kwargs={"project_id": self.project.id}), fetch_redirect_response=False)
        self.assertFalse(ProjectSpecialtyNeed.objects.filter(id=need.id).exists())
        self.assertFalse(ProjectSelection.objects.filter(id=self.selection.id).exists())
        self.assertTrue(ProjectSelection.objects.filter(id=other_selection.id).exists())


class ExecutorListTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="list-tester",
            password="test-password",
        )
        self.client.force_login(self.user)
        self.status = ExecutorStatus.objects.create(name="Активный")
        self.specialty_ar = Specialty.objects.create(code="АР", name="Архитектура")
        self.specialty_kr = Specialty.objects.create(code="КР", name="Конструкции")
        self.revit, _ = Software.objects.get_or_create(name="Revit")
        self.autocad, _ = Software.objects.get_or_create(name="AutoCAD")

        self.revit_executor = Executor.objects.create(
            last_name="Архитектор",
            first_name="Ревит",
            status=self.status,
        )
        self.revit_executor.software.add(self.revit)
        self.revit_executor.executor_specialties.create(specialty=self.specialty_ar)

        self.autocad_executor = Executor.objects.create(
            last_name="Конструктор",
            first_name="Автокад",
            status=self.status,
        )
        self.autocad_executor.software.add(self.autocad)
        self.autocad_executor.executor_specialties.create(specialty=self.specialty_kr)

    def test_filters_by_multiple_software_options(self):
        response = self.client.get(
            reverse("executor_list"),
            {"software": [str(self.revit.id), str(self.autocad.id)]},
        )

        self.assertContains(response, "Архитектор Ревит")
        self.assertContains(response, "Конструктор Автокад")

    def test_filters_by_specialty_checkboxes(self):
        response = self.client.get(
            reverse("executor_list"),
            {"specialty": [str(self.specialty_ar.id)]},
        )

        self.assertContains(response, "Архитектор Ревит")
        self.assertNotContains(response, "Конструктор Автокад")

    def test_list_uses_linked_name_contacts_and_resizable_columns(self):
        response = self.client.get(reverse("executor_list"))

        self.assertContains(response, "Контакты")
        self.assertContains(response, "data-resizable-table")
        self.assertContains(
            response,
            (
                f'<a class="executor-name-link" '
                f'href="/executors/{self.revit_executor.id}/">'
                "Архитектор Ревит</a>"
            ),
            html=True,
        )
        self.assertNotContains(response, "Открыть карточку")
        self.assertNotContains(response, "Открыть в админке")
