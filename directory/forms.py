from django import forms

from .models import (
    EmploymentType,
    Executor,
    ExecutorStatus,
    ObjectType,
    Project,
    ProjectSelection,
    SelectionStatus,
    Specialty,
)


class ProjectSelectionForm(forms.ModelForm):
    class Meta:
        model = ProjectSelection
        fields = (
            "specialty",
            "executor",
            "status",
            "offer_amount",
            "comment",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["specialty"].queryset = Specialty.objects.filter(
            is_active=True
        ).order_by("code")

        self.fields["executor"].queryset = Executor.objects.select_related(
            "status"
        ).order_by("last_name", "first_name", "middle_name")

        self.fields["status"].queryset = SelectionStatus.objects.filter(
            is_active=True
        ).order_by("name")

        self.fields["specialty"].label = "Специальность"
        self.fields["executor"].label = "Исполнитель"
        self.fields["status"].label = "Статус"
        self.fields["offer_amount"].label = "Сумма КП, руб."
        self.fields["comment"].label = "Комментарий"

        self.fields["offer_amount"].required = False
        self.fields["comment"].required = False

        self.fields["comment"].widget = forms.Textarea(
            attrs={
                "rows": 3,
            }
        )

from .models import EmploymentType, ExecutorStatus

class ExecutorForm(forms.ModelForm):
    specialties = forms.ModelMultipleChoiceField(
        label="Специальности",
        queryset=Specialty.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Executor
        fields = (
            "last_name",
            "first_name",
            "middle_name",
            "phone",
            "email",
            "messenger",
            "employment_type",
            "status",
            "works_in_revit",
            "revit_comment",
            "general_comment",
            "specialties",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["employment_type"].queryset = EmploymentType.objects.filter(
            is_active=True
        ).order_by("name")

        self.fields["status"].queryset = ExecutorStatus.objects.filter(
            is_active=True
        ).order_by("name")

        self.fields["specialties"].queryset = Specialty.objects.filter(
            is_active=True
        ).order_by("code")

        self.fields["middle_name"].required = False
        self.fields["phone"].required = False
        self.fields["email"].required = False
        self.fields["messenger"].required = False
        self.fields["employment_type"].required = False
        self.fields["revit_comment"].required = False
        self.fields["general_comment"].required = False

        self.fields["revit_comment"].widget = forms.Textarea(attrs={"rows": 3})
        self.fields["general_comment"].widget = forms.Textarea(attrs={"rows": 4})

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = (
            "name",
            "object_type",
            "area",
            "comment",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["object_type"].queryset = ObjectType.objects.filter(
            is_active=True
        ).order_by("name")

        self.fields["area"].required = False
        self.fields["comment"].required = False

        self.fields["comment"].widget = forms.Textarea(attrs={"rows": 4})