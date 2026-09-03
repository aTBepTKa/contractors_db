from django.db import migrations, models


def create_software_and_migrate_revit(apps, schema_editor):
    Executor = apps.get_model("directory", "Executor")
    Software = apps.get_model("directory", "Software")

    revit, _ = Software.objects.get_or_create(name="Revit")
    Software.objects.get_or_create(name="AutoCAD")

    for executor in Executor.objects.filter(works_in_revit=True).iterator():
        executor.software.add(revit)


def restore_revit_flag(apps, schema_editor):
    Executor = apps.get_model("directory", "Executor")

    Executor.objects.filter(software__name="Revit").update(works_in_revit=True)


class Migration(migrations.Migration):
    dependencies = [
        ("directory", "0003_projectspecialtyneed"),
    ]

    operations = [
        migrations.CreateModel(
            name="Software",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=100,
                        unique=True,
                        verbose_name="Наименование",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Активно"),
                ),
            ],
            options={
                "verbose_name": "Программное обеспечение",
                "verbose_name_plural": "Программное обеспечение",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="executor",
            name="software",
            field=models.ManyToManyField(
                blank=True,
                related_name="executors",
                to="directory.software",
                verbose_name="ПО",
            ),
        ),
        migrations.RenameField(
            model_name="executor",
            old_name="revit_comment",
            new_name="software_comment",
        ),
        migrations.AlterField(
            model_name="executor",
            name="software_comment",
            field=models.TextField(
                blank=True,
                help_text="Версии программ, уровень владения и особенности работы",
                verbose_name="Комментарий по ПО",
            ),
        ),
        migrations.RunPython(
            create_software_and_migrate_revit,
            restore_revit_flag,
        ),
        migrations.RemoveField(
            model_name="executor",
            name="works_in_revit",
        ),
    ]
