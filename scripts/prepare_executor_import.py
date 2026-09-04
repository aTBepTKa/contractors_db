"""Read the source XLSX and prepare a normalized JSON intermediate (no database writes)."""
import argparse
import json
import re
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import openpyxl


SPECIALTIES = {
    "Автоматизация": ("АиД", "Автоматизация и диспетчеризация"),
    "Внутренние системы водоснабжения и канализации": ("ВК", "Водоснабжение и канализация"),
    "Наружные сети водоснабжения и канализации": ("НВК", "Наружные сети водоснабжения и канализации"),
    "Отопление, вентиляция и кондиционирование": ("ОВ", "Отопление, вентиляция и кондиционирование"),
    "Охрана окружающей среды": ("ООС", "Охрана окружающей среды"),
    "Пожарная сигнализация": ("АПС", "Автоматическая пожарная сигнализация"),
    "Проводные средства связи внутренних сетей предприятий и организаций": ("СС", "Сети связи"),
    "Силовое электрооборудование и электрическое освещение (внутреннее)": ("ЭОМ", "Электрооборудование и электроосвещение"),
    "Системы пожаротушения и огнезащита": ("ПТО", "Системы пожаротушения и огнезащита"),
    "Сметная документация (второстепенно)": ("СМ", "Сметная документация"),
    "Тепломеханические решения": ("ТМ", "Тепломеханические решения"),
    "Тепломеханические решения тепловых сетей": ("ТС", "Тепломеханические решения тепловых сетей"),
    "Технология производства": ("ТХ", "Технологические решения"),
}
HEADERS = [
    "№ исходной записи", "Фамилия", "Имя", "Отчество", "Телефон", "Почта",
    "Тип занятости", "Статус", "Источник контакта", "Комментарий к источнику",
    "Город / местоположение", "Начал работать с", "Год рождения", "ПО",
    "Комментарий по ПО", "Специальности", "Общий комментарий",
]
PHONE = re.compile(r"(?<!\d)\+?[78][\s(\-]*\d{3}[\s)\-]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}(?!\d)")


def text(value):
    return str(value).strip() if value is not None else ""


def prepare(source, year):
    workbook = openpyxl.load_workbook(source, data_only=True)
    sheet = workbook["Для импорта"]
    result, audit = [], []
    all_software = set()
    for number, raw in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
        if not any(v is not None for v in raw):
            continue
        (source_id, last, first, middle, extra_source, source_name, source_comment,
         city, _description, raw_phone, email, raw_software, status, objects,
         raw_specialties, experience, birth, comment) = map(text, raw)
        notes = []
        if comment:
            notes.append(comment)
        if objects:
            notes.append("Опыт по типам объектов:\n" + objects)
        raw_email = email
        if raw_email:
            emails = re.findall(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", raw_email)
            if not emails:
                raise ValueError(f"Не распознана почта в строке {number}")
            email = emails[0].lower()
            if raw_email.lower() != email:
                notes.append("Дополнительные сведения о почте:\n" + raw_email)
        phones = PHONE.findall(raw_phone)
        phone = "+7" + re.sub(r"\D", "", phones[0])[1:] if phones else ""
        if raw_phone and raw_phone.lower() not in {"скрыт", "не указан"}:
            residual = PHONE.sub("", raw_phone).strip()
            if len(phones) > 1 or residual:
                notes.append("Дополнительные сведения о контактах:\n" + raw_phone)
            if not phones:
                raise ValueError(f"Не распознан телефон в строке {number}")
        source_notes = []
        if source_comment:
            source_notes.append(source_comment)
        if extra_source:
            if extra_source in {"общаемся в тг", "нет воцапа", "Только про ВК ему по эл. почте написал"}:
                notes.append("Дополнительные сведения о контактах:\n" + extra_source)
            else:
                source_notes.append("Дополнительно: " + extra_source)
        start_year = None
        if experience:
            value = experience.split(" из ")[0].replace(",", ".")
            rounded = int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            start_year = year - rounded
            if "," in experience or " из " in experience:
                audit.append({"row": number, "field": "Начал работать с", "before": experience, "after": start_year})
        birth_year = None
        if birth:
            birth_year = 1993 if birth == "193" else int(re.search(r"\d{4}", birth).group())
            if str(birth_year) != birth:
                audit.append({"row": number, "field": "Год рождения", "before": birth, "after": birth_year})
        programs = []
        software_notes = []
        for program in filter(None, (p.strip() for p in raw_software.split(","))):
            normalized = {"KAN CO 3.8": "KAN CO", "SANEXT SET 7.2": "SANEXT SET"}.get(program, program)
            programs.append(normalized)
            if normalized != program:
                software_notes.append(program)
        programs = list(dict.fromkeys(programs))
        all_software.update(programs)
        specialties = []
        for label in filter(None, (v.strip() for v in raw_specialties.split(";"))):
            specialties.append(SPECIALTIES[label][0])
            if "второстепенно" in label:
                notes.append("Специальности: сметная документация — второстепенно.")
        if not last or not first:
            audit.append({"row": number, "field": "ФИО", "before": [last, first], "after": [last or "Не указано", first or "Не указано"]})
        result.append([
            source_id, last or "Не указано", first or "Не указано", middle,
            phone, email, "Самозанятый", status.capitalize(), source_name,
            "\n\n".join(source_notes), city, start_year, birth_year,
            "; ".join(programs), "; ".join(software_notes),
            "; ".join(dict.fromkeys(specialties)), "\n\n".join(notes),
        ])
    for column in [0, 4, 5]:
        duplicates = [key for key, count in Counter(r[column] for r in result if r[column]).items() if count > 1]
        if duplicates:
            raise ValueError(f"Повторяющиеся значения в столбце {HEADERS[column]}: {duplicates}")
    assert len(result) == 113, len(result)
    assert all(len(r[4]) <= 50 and len(r[1]) <= 100 and len(r[2]) <= 100 for r in result)
    return {"headers": HEADERS, "rows": result, "reference_year": year,
            "software": sorted(all_software),
            "specialties": dict(SPECIALTIES.values()),
            "sources": sorted({r[8] for r in result}), "audit": audit,
            "summary": {"count": len(result), "no_phone": sum(not r[4] for r in result),
                        "no_specialty": sum(not r[15] for r in result),
                        "statuses": dict(Counter(r[7] for r in result))}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    data = prepare(args.source, args.year)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(data["summary"], ensure_ascii=False))
