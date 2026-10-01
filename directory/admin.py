from django.contrib import admin

from .models import (
    ContactSource,
    EmploymentType,
    Executor,
    ExecutorComment,
    ExecutorSpecialty,
    ExecutorStatus,
    ObjectType,
    Project,
    ProjectSelection,
    ProjectSpecialtyNeed,
    SelectionNegotiation,
    SelectionStatus,
    ProjectStatus,
    Software,
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

class ProjectSpecialtyNeedInline(admin.TabularInline):
    model = ProjectSpecialtyNeed
    extra = 0
    fields = (
        "specialty",
        "is_required",
        "comment",
        "created_by",
    )
    readonly_fields = (
        "created_by",
    )

class ProjectSelectionInline(admin.TabularInline):
    model = ProjectSelection
    extra = 1
    autocomplete_fields = ("specialty", "executor", "status")


class SelectionNegotiationInline(admin.TabularInline):
    model = SelectionNegotiation
    extra = 1
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)


@admin.register(ContactSource)
class ContactSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


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


@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(ProjectStatus)
class ProjectStatusAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Executor)
class ExecutorAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if "status" in form.changed_data:
            obj.status_changed_by = request.user
        super().save_model(request, obj, form, change)

    list_display = (
        "full_name",
        "specialties_list",
        "phone",
        "email",
        "messenger",
        "software_list",
        "status",
        "employment_type",
        "updated_at",
    )
    list_filter = (
        "status",
        "employment_type",
        "software",
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
    filter_horizontal = ("software",)
    inlines = (
        ExecutorSpecialtyInline,
        ExecutorCommentInline,
        ExecutorProjectSelectionInline,
    )

    fieldsets = (
        (
            "Источник и опыт",
            {"fields": ("contact_source", "source_comment", "city", "birth_year", "work_start_year")},
        ),
        (
            "ФИО",
            {
                "fields": (
                    ("last_name", "first_name", "middle_name"),
                )
            },
        ),
        (
            "Контакты",
            {
                "fields": (
                    ("phone", "email", "messenger"),
                )
            },
        ),
        (
            "Статус",
            {
                "fields": (
                    ("status", "employment_type"),
                    "status_comment",
                )
            },
        ),
        (
            "ПО",
            {
                "fields": (
                    "software",
                    "software_comment",
                )
            },
        ),
        (
            "Общие комментарии",
            {
                "fields": (
                    "general_comment",
                )
            },
        ),
        (
            "Служебные поля",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    class Media:
        css = {
            "all": ("directory/css/admin.css",)
        }    

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

    @admin.display(description="ПО")
    def software_list(self, obj):
        software = [item.name for item in obj.software.all()]
        return ", ".join(software) if software else "—"

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("executor_specialties__specialty", "software")
        )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "status",
        "object_type",
        "area",
        "selections_count",
        "updated_at",
    )
    list_filter = ("status", "object_type")
    search_fields = ("name", "comment")
    readonly_fields = ("created_at", "updated_at")
    inlines = [
        ProjectSpecialtyNeedInline,
        ProjectSelectionInline,
    ]

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
    
    
@admin.register(ProjectSpecialtyNeed)
class ProjectSpecialtyNeedAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "specialty",
        "is_required",
        "created_by",
        "updated_at",
    )
    list_filter = (
        "is_required",
        "specialty",
        "project",
    )
    search_fields = (
        "project__name",
        "specialty__code",
        "specialty__name",
        "comment",
    )
