from django.db import migrations


def create_read_only_group(apps, schema_editor):
    apps.get_model("auth", "Group").objects.using(schema_editor.connection.alias).get_or_create(
        name="Только просмотр"
    )


class Migration(migrations.Migration):
    dependencies = [("directory", "0007_import_reference_data")]
    operations = [migrations.RunPython(create_read_only_group, migrations.RunPython.noop)]
