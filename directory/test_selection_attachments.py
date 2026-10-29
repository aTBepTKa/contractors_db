from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import (
    Executor, ExecutorStatus, ObjectType, Project, ProjectSelection,
    ProjectSpecialtyNeed, SelectionAttachment, SelectionStatus, Specialty,
)


class SelectionAttachmentTests(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.settings_override = self.settings(MEDIA_ROOT=self.media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.user = get_user_model().objects.create_user(username="editor")
        self.viewer = get_user_model().objects.create_user(username="viewer")
        self.viewer.groups.add(Group.objects.get_or_create(name="Только просмотр")[0])
        specialty = Specialty.objects.create(code="АР", name="Архитектура")
        self.project = Project.objects.create(name="Проект", object_type=ObjectType.objects.create(name="Дом"))
        ProjectSpecialtyNeed.objects.create(project=self.project, specialty=specialty)
        self.selection = ProjectSelection.objects.create(
            project=self.project, specialty=specialty,
            executor=Executor.objects.create(last_name="Иванов", first_name="Иван", status=ExecutorStatus.objects.create(name="Активный")),
            status=SelectionStatus.objects.get_or_create(name="Новый")[0],
        )
        self.upload_url = reverse("upload_selection_attachments", args=[self.selection.pk])
        self.client.force_login(self.user)

    def upload(self, name="КП.pdf", content=b"%PDF-1.4 test"):
        return self.client.post(self.upload_url, {"files": [SimpleUploadedFile(name, content)]})

    def test_multiple_uploads_metadata_and_download(self):
        response = self.client.post(self.upload_url, {"files": [
            SimpleUploadedFile("КП.pdf", b"pdf"), SimpleUploadedFile("Цена.XLSX", b"xlsx"),
        ]})
        self.assertRedirects(response, f"/projects/{self.project.pk}/?specialty={self.selection.specialty_id}#selection-{self.selection.pk}")
        self.assertEqual(self.selection.attachments.count(), 2)
        attachment = self.selection.attachments.get(original_name="КП.pdf")
        self.assertEqual(attachment.uploaded_by, self.user)
        self.assertEqual(attachment.size, 3)
        response = self.client.get(reverse("download_selection_attachment", args=[attachment.pk]))
        self.assertEqual(b"".join(response.streaming_content), b"pdf")
        self.assertEqual(response["Content-Type"], "application/octet-stream")
        self.assertIn("attachment;", response["Content-Disposition"])
        page = self.client.get(reverse("project_detail", args=[self.project.pk]))
        self.assertContains(page, "КП.pdf")
        self.assertContains(page, "Файлы (2)")

    def test_duplicate_names_get_separate_storage_paths(self):
        self.upload()
        self.upload()
        paths = list(self.selection.attachments.values_list("file", flat=True))
        self.assertEqual(len(set(paths)), 2)
        self.assertTrue(all(Path(self.media.name, p).exists() for p in paths))

    def test_invalid_group_saves_nothing(self):
        response = self.client.post(self.upload_url, {"files": [
            SimpleUploadedFile("valid.pdf", b"pdf"), SimpleUploadedFile("bad.exe", b"exe"),
        ]}, follow=True)
        self.assertContains(response, "неподдерживаемый формат")
        self.assertFalse(SelectionAttachment.objects.exists())
        self.assertFalse(list(Path(self.media.name).rglob("*")))

    def test_size_limit_and_empty_files(self):
        with patch("directory.views.ATTACHMENT_MAX_SIZE", 3):
            self.assertEqual(self.upload(content=b"1234").status_code, 302)
            self.assertFalse(SelectionAttachment.objects.exists())
            self.upload(content=b"123")
            self.assertEqual(SelectionAttachment.objects.count(), 1)
        self.upload(name="empty.pdf", content=b"")
        self.assertEqual(SelectionAttachment.objects.count(), 1)

    def test_no_files_reports_error(self):
        response = self.client.post(self.upload_url, follow=True)
        self.assertContains(response, "Выберите файлы")
        self.assertFalse(SelectionAttachment.objects.exists())

    def test_authenticated_access_and_read_only_permissions(self):
        self.upload()
        attachment = SelectionAttachment.objects.get()
        download = reverse("download_selection_attachment", args=[attachment.pk])
        delete = reverse("delete_selection_attachment", args=[attachment.pk])
        self.client.logout()
        for url, method in [(download, "get"), (delete, "post"), (self.upload_url, "post")]:
            self.assertEqual(getattr(self.client, method)(url).status_code, 302)
        self.client.force_login(self.viewer)
        response = self.client.get(download)
        self.assertEqual(response.status_code, 200)
        response.close()
        self.assertEqual(self.upload().status_code, 403)
        self.assertEqual(self.client.post(delete).status_code, 403)
        page = self.client.get(reverse("project_detail", args=[self.project.pk]))
        self.assertContains(page, "КП.pdf")
        self.assertNotContains(page, 'name="files"')
        self.assertNotContains(page, delete)

    def test_delete_removes_file_after_commit_and_keeps_other_files(self):
        self.upload()
        attachment = SelectionAttachment.objects.get()
        self.upload()
        path = Path(attachment.file.path)
        delete = reverse("delete_selection_attachment", args=[attachment.pk])
        self.assertEqual(self.client.get(delete).status_code, 405)
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.client.post(delete).status_code, 302)
        self.assertFalse(path.exists())
        self.assertEqual(SelectionAttachment.objects.count(), 1)
        self.assertTrue(Path(SelectionAttachment.objects.get().file.path).exists())

    def test_selection_cascade_removes_storage_file(self):
        self.upload()
        path = Path(SelectionAttachment.objects.get().file.path)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("delete_project_selection", args=[self.selection.pk]))
        self.assertFalse(SelectionAttachment.objects.exists())
        self.assertFalse(path.exists())

    def test_storage_files_cleaned_up_when_database_save_fails(self):
        with patch.object(SelectionAttachment, "save", side_effect=RuntimeError("database failure")):
            with self.assertRaises(RuntimeError):
                self.upload()
        self.assertFalse(SelectionAttachment.objects.exists())
        self.assertFalse([p for p in Path(self.media.name).rglob("*") if p.is_file()])

    def test_missing_attachment_and_missing_storage_file(self):
        self.assertEqual(self.client.get(reverse("download_selection_attachment", args=[99999])).status_code, 404)
        self.upload()
        attachment = SelectionAttachment.objects.get()
        Path(attachment.file.path).unlink()
        self.assertEqual(self.client.get(reverse("download_selection_attachment", args=[attachment.pk])).status_code, 404)

    def test_methods_and_unknown_selection(self):
        self.assertEqual(self.client.get(self.upload_url).status_code, 405)
        self.assertEqual(self.client.post(reverse("upload_selection_attachments", args=[99999])).status_code, 404)
