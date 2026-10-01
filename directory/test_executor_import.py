import csv
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from .forms import ExecutorForm
from .management.commands.import_executors import HEADERS, read_xlsx
from .models import EmploymentType, Executor, ExecutorStatus, Specialty


class ExecutorImportTests(TestCase):
    def setUp(self):
        ExecutorStatus.objects.get_or_create(name="Активный")
        Specialty.objects.get_or_create(code="ВК", defaults={"name": "Водоснабжение и канализация"})
        self.row = {h: "" for h in HEADERS}
        self.row.update({
            "№ исходной записи": "1", "Фамилия": "Проверочный", "Имя": "Исполнитель",
            "Телефон": "+79990000001", "Почта": "test@example.com", "Статус": "Активный",
            "Источник контакта": "HH.ru", "Начал работать с": "2014", "Год рождения": "1993",
            "ПО": "Revit; MagiCAD", "Специальности": "ВК; НВК",
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
        invalid = dict(self.row, **{"№ исходной записи": "2", "Почта": "invalid"})
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
