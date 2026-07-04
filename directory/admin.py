from django.contrib import admin

from .models import (
    EmploymentType,
    Executor,
    ExecutorComment,
    ExecutorSpecialty,
    ExecutorStatus,
    ObjectType,
    Project,
    ProjectSelection,
    SelectionNegotiation,
    SelectionStatus,
    Specialty,
)


def format_money(value):
    if value is None:
        return "—"
    return f"{value:,}".replace(",", " ")


class ExecutorSpecialtyInline(admin.TabularInline):
    model = ExecutorSpecialty
    extra = 1
    autocomplete_fields = ("specialty",)


class ExecutorCommentInline(admin.TabularInline):
    model = ExecutorComment
    extra = 0
    readonly_fields = ("created_at",)
    autocomplete_fields = ("project", "user")


class ExecutorProjectSelectionInline(admin.TabularInline):
    model = ProjectSelection
    extra = 0
    fields = (
        "project",
        "specialty",
        "status",
        "formatted_offer_amount",
        "comment",
        "updated_at",
    )
    readonly_fields = (
        "project",
        "specialty",
        "status",
        "formatted_offer_amount",
        "comment",
        "updated_at",
    )
    can_delete = False
    show_change_link = True
    verbose_name = "Участие в подборе"
    verbose_name_plural = "История подбора по проектам"

    @admin.display(description="Сумма КП, руб.")
    def formatted_offer_amount(self, obj):
        return format_money(obj.offer_amount)

    def has_add_permission(self, request, obj=None):
        return False


class ProjectSelectionInline(admin.TabularInline):
    model = ProjectSelection
    extra = 1
    autocomplete_fields = ("specialty", "executor", "status")


class SelectionNegotiationInline(admin.TabularInline):
    model = SelectionNegotiation
    extra = 1
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)


@admin.register(EmploymentType)
class EmploymentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(ExecutorStatus)
class ExecutorStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(ObjectType)
class ObjectTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(SelectionStatus)
class SelectionStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Executor)
class ExecutorAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "specialties_list",
        "phone",
        "email",
        "messenger",
        "works_in_revit",
        "status",
        "employment_type",
        "updated_at",
    )
    list_filter = (
        "status",
        "employment_type",
        "works_in_revit",
        "executor_specialties__specialty",
    )
    search_fields = (
        "last_name",
        "first_name",
        "middle_name",
        "phone",
        "email",
        "messenger",
        "general_comment",
    )
    readonly_fields = ("created_at", "updated_at")
    inlines = (
        ExecutorSpecialtyInline,
        ExecutorCommentInline,
        ExecutorProjectSelectionInline,
    )

    fieldsets = (
        (
            "ФИО и контакты",
            {
                "fields": (
                    "last_name",
                    "first_name",
                    "middle_name",
                    "phone",
                    "email",
                    "messenger",
                    "employment_type",
                )
            },
        ),
        (
            "Revit",
            {
                "fields": (
                    "works_in_revit",
                    "revit_comment",
                )
            },
        ),
        (
            "Статус и комментарии",
            {
                "fields": (
                    "status",
                    "status_comment",
                    "general_comment",
                )
            },
        ),
        (
            "Служебные поля",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="ФИО", ordering="last_name")
    def full_name(self, obj):
        return str(obj)

    @admin.display(description="Специальности")
    def specialties_list(self, obj):
        specialties = [
            item.specialty.code
            for item in obj.executor_specialties.select_related("specialty").all()
        ]
        return ", ".join(specialties) if specialties else "—"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("executor_specialties__specialty")
        )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "object_type",
        "area",
        "selections_count",
        "updated_at",
    )
    list_filter = ("object_type",)
    search_fields = ("name", "comment")
    readonly_fields = ("created_at", "updated_at")
    inlines = (ProjectSelectionInline,)

    @admin.display(description="Строк подбора")
    def selections_count(self, obj):
        return obj.selections.count()


@admin.register(ProjectSelection)
class ProjectSelectionAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "specialty",
        "executor",
        "status",
        "formatted_offer_amount",
        "updated_at",
    )
    list_filter = (
        "project",
        "specialty",
        "status",
        "executor",
    )
    search_fields = (
        "project__name",
        "executor__last_name",
        "executor__first_name",
        "executor__middle_name",
        "comment",
    )
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("project", "specialty", "executor", "status")
    inlines = (SelectionNegotiationInline,)

    @admin.display(description="Сумма КП, руб.", ordering="offer_amount")
    def formatted_offer_amount(self, obj):
        return format_money(obj.offer_amount)


@admin.register(SelectionNegotiation)
class SelectionNegotiationAdmin(admin.ModelAdmin):
    list_display = ("selection", "event_date", "user", "created_at")
    list_filter = ("event_date", "user")
    search_fields = (
        "selection__project__name",
        "selection__executor__last_name",
        "selection__executor__first_name",
        "comment",
    )
    readonly_fields = ("created_at",)
    autocomplete_fields = ("selection", "user")


@admin.register(ExecutorComment)
class ExecutorCommentAdmin(admin.ModelAdmin):
    list_display = ("executor", "project", "user", "created_at")
    list_filter = ("project", "user", "created_at")
    search_fields = (
        "executor__last_name",
        "executor__first_name",
        "executor__middle_name",
        "comment",
    )
    readonly_fields = ("created_at",)
    autocomplete_fields = ("executor", "project", "user")