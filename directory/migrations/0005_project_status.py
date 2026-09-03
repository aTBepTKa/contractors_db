from django.db import migrations, models
import django.db.models.deletion


def seed_project_statuses(apps, schema_editor):
    ProjectStatus = apps.get_model("directory", "ProjectStatus")
    Project = apps.get_model("directory", "Project")

    draft, _ = ProjectStatus.objects.get_or_create(name="Черновик")
    in_progress, _ = ProjectStatus.objects.get_or_create(name="В работе")
    ProjectStatus.objects.get_or_create(name="Завершен")

    Project.objects.filter(status__isnull=True).update(status=in_progress)


class Migration(migrations.Migration):
    dependencies = [
        ("directory", "0004_software_and_executor_software"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProjectStatus",
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
                        max_length=50,
                        unique=True,
                        verbose_name="Наименование",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Активен"),
                ),
            ],
            options={
                "verbose_name": "Статус проекта",
                "verbose_name_plural": "Статусы проектов",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="project",
            name="status",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="projects",
                to="directory.projectstatus",
                verbose_name="Статус проекта",
            ),
        ),
        migrations.RunPython(seed_project_statuses, migrations.RunPython.noop),
    ]
