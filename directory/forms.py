from django import forms

from .models import Executor, ProjectSelection, SelectionStatus, Specialty


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