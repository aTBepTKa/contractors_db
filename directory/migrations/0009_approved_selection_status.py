from django.db import migrations


def add_approved_status(apps, schema_editor):
    apps.get_model("directory", "SelectionStatus").objects.using(
        schema_editor.connection.alias
    ).get_or_create(name="Утвержден", defaults={"is_active": True})


class Migration(migrations.Migration):
    dependencies = [("directory", "0008_read_only_group")]
    operations = [migrations.RunPython(add_approved_status, migrations.RunPython.noop)]
