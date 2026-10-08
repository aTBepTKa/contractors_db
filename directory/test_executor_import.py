import csv
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape
from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .forms import ExecutorForm
from .management.commands.import_executors import HEADERS, LEGACY_HEADERS, read_xlsx
from .models import EmploymentType, Executor, ExecutorStatus, Specialty


class ExecutorImportTests(TestCase):
    def setUp(self):
        ExecutorStatus.objects.get_or_create(name="Активный")
        Specialty.objects.get_or_create(code="ВК", defaults={"name": "Водоснабжение и канализация"})
        self.row = {h: "" for h in HEADERS}
        self.row.update({
            "Фамилия": "Проверочный", "Имя": "Исполнитель",
            "Телефон": "+79990000001", "Почта": "test@example.com", "Статус": "Активный",
            "Источник контакта": "HH.ru", "Начал работать с": "2014", "Год рождения": "1993",
            "ПО": "revit; MAGICAD", "Специальности": "вк; нвк",
            "Общий комментарий": 'Контакты: "Telegram"; дополнительный номер\nОпыт: общественные здания',
        })
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "executors.csv"

    def write_rows(self, rows):
        with self.path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=HEADERS, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)

    def write_xlsx_rows(self, rows, headers=HEADERS):
        path = Path(self.temp.name) / "executors.xlsx"
        matrix = [headers] + [[row.get(header, "") for header in headers] for row in rows]
        xml_rows = []
        for row_number, values in enumerate(matrix, 1):
            cells = "".join(
                f'<c r="{chr(65 + index)}{row_number}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
                for index, value in enumerate(values)
            )
            xml_rows.append(f'<row r="{row_number}">{cells}</row>')
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            archive.writestr(
                "xl/workbook.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="Для импорта" sheetId="1" r:id="rId1"/></sheets></workbook>',
            )
            archive.writestr(
                "xl/_rels/workbook.xml.rels",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                'Target="/xl/worksheets/sheet1.xml"/></Relationships>',
            )
            archive.writestr(
                "xl/worksheets/sheet1.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'<sheetData>{"".join(xml_rows)}</sheetData></worksheet>',
            )
        return path

    def test_xlsx_absolute_sheet_target_is_supported(self):
        path = Path(self.temp.name) / "template.xlsx"
        header_cells = "".join(
            f'<c r="{chr(65 + index)}1" t="inlineStr"><is><t>{value}</t></is></c>'
            for index, value in enumerate(HEADERS)
        )
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            archive.writestr(
                "xl/workbook.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="Для импорта" sheetId="1" r:id="rId1"/></sheets></workbook>',
            )
            archive.writestr(
                "xl/_rels/workbook.xml.rels",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                'Target="/xl/worksheets/sheet1.xml"/></Relationships>',
            )
            archive.writestr(
                "xl/worksheets/sheet1.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'<sheetData><row r="1">{header_cells}</row></sheetData></worksheet>',
            )
        headers, rows = read_xlsx(path)
        self.assertEqual(headers, list(HEADERS))
        self.assertEqual(rows, [])

    def test_dry_run_does_not_create_executors(self):
        self.write_rows([self.row])
        call_command("import_executors", str(self.path), stdout=StringIO())
        self.assertEqual(Executor.objects.count(), 0)

    def test_legacy_xlsx_with_source_number_is_still_supported(self):
        legacy_row = {**self.row, "№ исходной записи": "42"}
        path = self.write_xlsx_rows([legacy_row], LEGACY_HEADERS)

        call_command("import_executors", str(path), apply=True, stdout=StringIO())

        self.assertEqual(Executor.objects.count(), 1)

    def test_apply_preserves_fields_and_relations_and_rejects_repeat(self):
        self.write_rows([self.row])
        call_command("import_executors", str(self.path), apply=True, stdout=StringIO())
        obj = Executor.objects.get()
        self.assertEqual(obj.phone, "+79990000001")
        self.assertEqual(obj.birth_year, 1993)
        self.assertEqual(obj.work_start_year, 2014)
        self.assertEqual(obj.employment_type.name, "Самозанятый")
        self.assertEqual(obj.contact_source.name, "HH.ru")
        self.assertEqual(obj.general_comment, self.row["Общий комментарий"])
        self.assertEqual(set(obj.software.values_list("name", flat=True)), {"Revit", "MagiCAD"})
        self.assertEqual(set(obj.executor_specialties.values_list("specialty__code", flat=True)), {"ВК", "НВК"})
        with self.assertRaises(CommandError):
            call_command("import_executors", str(self.path), apply=True, stdout=StringIO())
        self.assertEqual(Executor.objects.count(), 1)

    def test_invalid_later_row_leaves_database_unchanged(self):
        invalid = dict(
            self.row,
            **{"Фамилия": "Другой", "Телефон": "+79990000002", "Почта": "invalid"},
        )
        self.write_rows([self.row, invalid])
        with self.assertRaises(CommandError):
            call_command("import_executors", str(self.path), apply=True, stdout=StringIO())
        self.assertEqual(Executor.objects.count(), 0)

    def test_employment_default_does_not_overwrite_existing_choice(self):
        default = EmploymentType.objects.get(name="Самозанятый")
        self.assertEqual(ExecutorForm().initial["employment_type"], default.pk)
        other = EmploymentType.objects.create(name="ИП")
        obj = Executor.objects.create(last_name="Тест", first_name="Тест", employment_type=other,
                                      status=ExecutorStatus.objects.get(name="Активный"))
        self.assertEqual(ExecutorForm(instance=obj).initial["employment_type"], other.pk)


class ExecutorImportViewTests(ExecutorImportTests):
    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create_user(username="importer")
        self.client.force_login(self.user)

    def test_template_download_returns_xlsx(self):
        response = self.client.get(reverse("executor_import_template"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("Шаблон_импорта_исполнителей.xlsx", unquote(response["Content-Disposition"]))
        self.assertTrue(b"".join(response.streaming_content).startswith(b"PK"))

    def test_upload_previews_then_confirmation_imports(self):
        path = self.write_xlsx_rows([self.row])
        upload = SimpleUploadedFile(
            "executors.xlsx", path.read_bytes(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        preview = self.client.post(reverse("executor_import"), {"file": upload})

        self.assertEqual(preview.status_code, 200)
        self.assertContains(preview, "Будет добавлено: 1")
        self.assertContains(preview, "Проверочный Исполнитель")
        self.assertEqual(Executor.objects.count(), 0)
        self.assertIn("executor_import_rows", self.client.session)

        result = self.client.post(reverse("executor_import_confirm"))

        self.assertRedirects(result, reverse("executor_list"), fetch_redirect_response=False)
        self.assertEqual(Executor.objects.count(), 1)
        self.assertNotIn("executor_import_rows", self.client.session)

    def test_duplicate_is_rejected_before_preview(self):
        Executor.objects.create(
            last_name=self.row["Фамилия"], first_name=self.row["Имя"],
            status=ExecutorStatus.objects.get(name="Активный"),
        )
        path = self.write_xlsx_rows([self.row])
        upload = SimpleUploadedFile("executors.xlsx", path.read_bytes())

        response = self.client.post(reverse("executor_import"), {"file": upload})

        self.assertContains(response, "автоматическая перезапись запрещена")
        self.assertNotContains(response, "Подтвердить импорт")
        self.assertNotIn("executor_import_rows", self.client.session)

    def test_confirmation_revalidates_if_duplicate_appears_after_preview(self):
        path = self.write_xlsx_rows([self.row])
        upload = SimpleUploadedFile("executors.xlsx", path.read_bytes())
        preview = self.client.post(reverse("executor_import"), {"file": upload})
        self.assertContains(preview, "Будет добавлено: 1")
        Executor.objects.create(
            last_name=self.row["Фамилия"], first_name=self.row["Имя"],
            status=ExecutorStatus.objects.get(name="Активный"),
        )

        response = self.client.post(reverse("executor_import_confirm"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Импорт отменён")
        self.assertEqual(Executor.objects.count(), 1)
        self.assertNotIn("executor_import_rows", self.client.session)
