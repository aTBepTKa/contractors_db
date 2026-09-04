from django.db import migrations


def seed_references(apps, schema_editor):
    db = schema_editor.connection.alias
    source = apps.get_model("directory", "ContactSource")
    for name in ["HH.ru", "Рекомендация", "Существующий", "Другое"]:
        source.objects.using(db).get_or_create(name=name)
    apps.get_model("directory", "EmploymentType").objects.using(db).get_or_create(name="Самозанятый")
    software = apps.get_model("directory", "Software")
    for name in [
        "3ds Max", "AVEVA PDMS", "Audytor", "Audytor CO", "Audytor OZC", "AutoCAD",
        "AutoCAD Plant 3D", "Civil 3D", "DCAD", "Danfoss С.О.", "KAN CO", "MagiCAD",
        "Model Studio CS", "Navisworks", "Oventrop", "Refprop", "Rehau Rauwin",
        "Renga", "Revit", "SANEXT SET", "SOLIDWORKS", "SPDS", "SketchUp", "Solibri",
        "V-Ray", "Valtec", "nanoCAD", "АРС-ПС", "Гранд-смета", "КВМ-Лаб", "КВМ-дым", "КОМПАС-3D",
    ]:
        software.objects.using(db).get_or_create(name=name)
    specialty = apps.get_model("directory", "Specialty")
    for code, name in [
        ("НВК", "Наружные сети водоснабжения и канализации"),
        ("ООС", "Охрана окружающей среды"),
        ("ПТО", "Системы пожаротушения и огнезащита"),
        ("ТМ", "Тепломеханические решения"),
        ("ТС", "Тепломеханические решения тепловых сетей"),
    ]:
        specialty.objects.using(db).get_or_create(code=code, defaults={"name": name})


class Migration(migrations.Migration):
    dependencies = [("directory", "0006_executor_import_fields")]
    operations = [migrations.RunPython(seed_references, migrations.RunPython.noop)]
