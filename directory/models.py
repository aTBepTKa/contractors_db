from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class ContactSource(models.Model):
    name = models.CharField("Наименование", max_length=100, unique=True)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Источник контакта"
        verbose_name_plural = "Источники контактов"
        ordering = ["name"]

    def __str__(self):
        return self.name


class EmploymentType(models.Model):
    name = models.CharField(
        "Наименование",
        max_length=100,
        unique=True,
    )
    is_active = models.BooleanField(
        "Активен",
        default=True,
    )

    class Meta:
        verbose_name = "Тип занятости"
        verbose_name_plural = "Типы занятости"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ExecutorStatus(models.Model):
    name = models.CharField(
        "Наименование",
        max_length=100,
        unique=True,
    )
    is_active = models.BooleanField(
        "Активен",
        default=True,
    )

    class Meta:
        verbose_name = "Статус исполнителя"
        verbose_name_plural = "Статусы исполнителей"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Software(models.Model):
    name = models.CharField(
        "Наименование",
        max_length=100,
        unique=True,
    )
    is_active = models.BooleanField(
        "Активно",
        default=True,
    )

    class Meta:
        verbose_name = "Программное обеспечение"
        verbose_name_plural = "Программное обеспечение"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Executor(models.Model):
    status_changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        editable=False, related_name="executor_status_changes", verbose_name="Статус изменил",
    )
    contact_source = models.ForeignKey(
        ContactSource, verbose_name="Источник контакта", on_delete=models.PROTECT,
        null=True, blank=True, related_name="executors",
    )
    source_comment = models.TextField("Комментарий к источнику", blank=True)
    city = models.CharField("Город / местоположение", max_length=255, blank=True)
    work_start_year = models.PositiveSmallIntegerField(
        "Начал работать с", null=True, blank=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
    )
    birth_year = models.PositiveSmallIntegerField(
        "Год рождения", null=True, blank=True,
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
    )
    last_name = models.CharField(
        "Фамилия",
        max_length=100,
    )
    first_name = models.CharField(
        "Имя",
        max_length=100,
    )
    middle_name = models.CharField(
        "Отчество",
        max_length=100,
        blank=True,
    )
    email = models.EmailField(
        "Почта",
        blank=True,
    )
    phone = models.CharField(
        "Телефон",
        max_length=50,
        blank=True,
    )
    messenger = models.CharField(
        "Мессенджер",
        max_length=150,
        blank=True,
        help_text="Telegram, WhatsApp или другой способ связи",
    )
    employment_type = models.ForeignKey(
        EmploymentType,
        verbose_name="Тип занятости",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="executors",
    )
    software = models.ManyToManyField(
        Software,
        verbose_name="ПО",
        blank=True,
        related_name="executors",
    )
    software_comment = models.TextField(
        "Комментарий по ПО",
        blank=True,
        help_text="Версии программ, уровень владения и особенности работы",
    )
    status = models.ForeignKey(
        ExecutorStatus,
        verbose_name="Статус",
        on_delete=models.PROTECT,
        related_name="executors",
    )
    status_comment = models.TextField(
        "Комментарий к статусу",
        blank=True,
        help_text="Причина, почему не работаем или есть ограничения",
    )
    general_comment = models.TextField(
        "Общий комментарий",
        blank=True,
    )
    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "Дата изменения",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Исполнитель"
        verbose_name_plural = "Исполнители"
        ordering = ["last_name", "first_name", "middle_name"]

    def __str__(self):
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(part for part in parts if part)


class Specialty(models.Model):
    code = models.CharField(
        "Код",
        max_length=30,
        unique=True,
        help_text="Например: АР, КР, ОВ, ВК, ЭОМ",
    )
    name = models.CharField(
        "Наименование",
        max_length=255,
    )
    is_active = models.BooleanField(
        "Активна",
        default=True,
    )

    class Meta:
        verbose_name = "Специальность"
        verbose_name_plural = "Специальности"
        ordering = ["code"]

    def __str__(self):
        return self.code


class ExecutorSpecialty(models.Model):
    executor = models.ForeignKey(
        Executor,
        verbose_name="Исполнитель",
        on_delete=models.CASCADE,
        related_name="executor_specialties",
    )
    specialty = models.ForeignKey(
        Specialty,
        verbose_name="Специальность",
        on_delete=models.PROTECT,
        related_name="executor_specialties",
    )

    class Meta:
        verbose_name = "Специальность исполнителя"
        verbose_name_plural = "Специальности исполнителей"
        constraints = [
            models.UniqueConstraint(
                fields=["executor", "specialty"],
                name="unique_executor_specialty",
            )
        ]

    def __str__(self):
        return f"{self.executor} — {self.specialty}"


class ObjectType(models.Model):
    name = models.CharField(
        "Наименование",
        max_length=150,
        unique=True,
    )
    is_active = models.BooleanField(
        "Активен",
        default=True,
    )

    class Meta:
        verbose_name = "Тип объекта"
        verbose_name_plural = "Типы объектов"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProjectStatus(models.Model):
    name = models.CharField(
        "Наименование",
        max_length=50,
        unique=True,
    )
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Статус проекта"
        verbose_name_plural = "Статусы проектов"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Наименование объекта",
    )

    object_type = models.ForeignKey(
        ObjectType,
        on_delete=models.PROTECT,
        related_name="projects",
        verbose_name="Тип объекта",
    )

    status = models.ForeignKey(
        ProjectStatus,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="projects",
        verbose_name="Статус проекта",
    )

    chief_project_engineer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="managed_projects",
        verbose_name="ГИП",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_projects",
        verbose_name="Создал",
    )

    area = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Площадь, м²",
    )

    comment = models.TextField(
        blank=True,
        verbose_name="Комментарий",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
    )

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = ["name"]

    def __str__(self):
        return self.name

class ProjectSpecialtyNeed(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="specialty_needs",
        verbose_name="Проект",
    )

    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        related_name="project_needs",
        verbose_name="Специальность",
    )

    is_required = models.BooleanField(
        default=True,
        verbose_name="Требуется",
    )

    comment = models.TextField(
        blank=True,
        verbose_name="Комментарий",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_project_specialty_needs",
        verbose_name="Создал",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
    )

    class Meta:
        verbose_name = "Потребность проекта по разделу"
        verbose_name_plural = "Потребности проектов по разделам"
        ordering = ["project__name", "specialty__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "specialty"],
                name="unique_project_specialty_need",
            )
        ]

    def __str__(self):
        return f"{self.project} — {self.specialty}"

class ExecutorComment(models.Model):
    executor = models.ForeignKey(
        Executor,
        verbose_name="Исполнитель",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    project = models.ForeignKey(
        Project,
        verbose_name="Проект",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="executor_comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.PROTECT,
        related_name="executor_comments",
    )
    comment = models.TextField(
        "Комментарий",
    )
    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Комментарий к исполнителю"
        verbose_name_plural = "Комментарии к исполнителям"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.executor} — {self.created_at:%d.%m.%Y}"


class SelectionStatus(models.Model):
    name = models.CharField(
        "Наименование",
        max_length=100,
        unique=True,
    )
    is_active = models.BooleanField(
        "Активен",
        default=True,
    )

    class Meta:
        verbose_name = "Статус подбора"
        verbose_name_plural = "Статусы подбора"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProjectSelection(models.Model):
    project = models.ForeignKey(
        Project,
        verbose_name="Проект",
        on_delete=models.CASCADE,
        related_name="selections",
    )
    specialty = models.ForeignKey(
        Specialty,
        verbose_name="Специальность",
        on_delete=models.PROTECT,
        related_name="project_selections",
    )
    executor = models.ForeignKey(
        Executor,
        verbose_name="Исполнитель",
        on_delete=models.PROTECT,
        related_name="project_selections",
    )
    status = models.ForeignKey(
        SelectionStatus,
        verbose_name="Статус",
        on_delete=models.PROTECT,
        related_name="project_selections",
    )
    offer_amount = models.PositiveIntegerField(
        "Сумма КП, руб.",
        null=True,
        blank=True,
        help_text="Хранится без копеек. Например: 200000. В интерфейсе будет отображаться как 200 000.",
    )
    comment = models.TextField(
        "Комментарий",
        blank=True,
    )
    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "Дата изменения",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Подбор исполнителя"
        verbose_name_plural = "Подбор исполнителей"
        ordering = ["project", "specialty", "executor"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "specialty", "executor"],
                name="unique_project_specialty_executor",
            )
        ]

    def __str__(self):
        return f"{self.project} — {self.specialty} — {self.executor}"


class SelectionNegotiation(models.Model):
    selection = models.ForeignKey(
        ProjectSelection,
        verbose_name="Строка подбора",
        on_delete=models.CASCADE,
        related_name="negotiations",
    )
    event_date = models.DateField(
        "Дата события",
    )
    comment = models.TextField(
        "Комментарий",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Пользователь",
        on_delete=models.PROTECT,
        related_name="selection_negotiations",
    )
    created_at = models.DateTimeField(
        "Дата создания записи",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Переговоры по подбору"
        verbose_name_plural = "Переговоры по подбору"
        ordering = ["-event_date", "-created_at"]

    def __str__(self):
        return f"{self.selection} — {self.event_date:%d.%m.%Y}"
