"""Validate or import the prepared UTF-8 CSV. Existing executors are never overwritten."""
import csv
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from directory.models import (
    ContactSource, EmploymentType, Executor, ExecutorSpecialty, ExecutorStatus,
    Software, Specialty,
)


FIELDS = {
    "Фамилия": "last_name", "Имя": "first_name", "Отчество": "middle_name",
    "Телефон": "phone", "Почта": "email", "Комментарий к источнику": "source_comment",
    "Город / местоположение": "city", "Комментарий по ПО": "software_comment",
    "Общий комментарий": "general_comment",
}
HEADERS = set(FIELDS) | {"№ исходной записи", "Тип занятости", "Статус", "Источник контакта",
                          "Начал работать с", "Год рождения", "ПО", "Специальности"}


def lookup(model, value, key="name", optional=False):
    if not value and optional:
        return None
    try:
        return model.objects.get(**{key: value, "is_active": True})
    except model.DoesNotExist:
        raise ValueError(f"{model._meta.verbose_name}: неизвестное или неактивное значение «{value}»")


def validate_rows(rows):
    prepared, errors = [], []
    seen = {key: set() for key in ["source_id", "phone", "email", "name"]}
    existing_phones = set(Executor.objects.exclude(phone="").values_list("phone", flat=True))
    existing_emails = {v.lower() for v in Executor.objects.exclude(email="").values_list("email", flat=True)}
    existing_names = {tuple(v.casefold() for v in parts) for parts in Executor.objects.values_list("last_name", "first_name", "middle_name")}
    for index, row in enumerate(rows, 2):
        try:
            if None in row or any(v is None for v in row.values()):
                raise ValueError("Количество столбцов не совпадает с заголовком")
            values = {field: row[label].strip() for label, field in FIELDS.items()}
            values["email"] = values["email"].lower()
            for label, field in [("Начал работать с", "work_start_year"), ("Год рождения", "birth_year")]:
                values[field] = int(row[label]) if row[label].strip() else None
            values["employment_type"] = lookup(EmploymentType, row["Тип занятости"].strip() or "Самозанятый")
            values["status"] = lookup(ExecutorStatus, row["Статус"].strip())
            values["contact_source"] = lookup(ContactSource, row["Источник контакта"].strip(), optional=True)
            obj = Executor(**values)
            obj.full_clean()
            programs = [lookup(Software, name.strip()) for name in row["ПО"].split(";") if name.strip()]
            specialties = [lookup(Specialty, code.strip(), key="code") for code in row["Специальности"].split(";") if code.strip()]
            source_id = row["№ исходной записи"].strip()
            if not source_id:
                raise ValueError("Не указан номер исходной записи")
            keys = {"source_id": source_id, "phone": obj.phone, "email": obj.email,
                    "name": tuple(getattr(obj, f).casefold() for f in ["last_name", "first_name", "middle_name"])}
            for key, value in keys.items():
                if value and value in seen[key]:
                    raise ValueError(f"Повторяющееся значение {key} в файле")
                if value:
                    seen[key].add(value)
            if (obj.phone and obj.phone in existing_phones) or (obj.email and obj.email in existing_emails) or keys["name"] in existing_names:
                raise ValueError("Совпадение с существующим исполнителем; автоматическая перезапись запрещена")
            prepared.append((obj, programs, specialties))
        except (ValueError, ValidationError) as exc:
            errors.append(f"Строка {index}: {exc}")
    if errors:
        raise CommandError("\n".join(errors))
    return prepared


class Command(BaseCommand):
    help = "Проверить подготовленный CSV; --apply сохраняет исполнителей одной транзакцией."

    def add_arguments(self, parser):
        parser.add_argument("path", type=Path)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        try:
            with options["path"].open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream, delimiter=";")
                if not reader.fieldnames or set(reader.fieldnames) != HEADERS or len(reader.fieldnames) != len(HEADERS):
                    raise CommandError("Неверный набор столбцов CSV")
                rows = list(reader)
        except (OSError, UnicodeError, csv.Error) as exc:
            raise CommandError(str(exc)) from exc
        if not rows:
            raise CommandError("Файл не содержит исполнителей")
        with transaction.atomic():
            if options["apply"]:
                # Serialize this importer so two simultaneous runs cannot add the same file.
                list(ExecutorStatus.objects.select_for_update().order_by("pk"))
            prepared = validate_rows(rows)
            if options["apply"]:
                for obj, programs, specialties in prepared:
                    obj.save()
                    obj.software.set(programs)
                    for specialty in set(specialties):
                        ExecutorSpecialty.objects.create(executor=obj, specialty=specialty)
        verb = "Импортировано" if options["apply"] else "Проверено без записи в базу"
        self.stdout.write(self.style.SUCCESS(f"{verb}: {len(prepared)} исполнителей."))
