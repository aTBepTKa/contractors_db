from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Executor, Project, ProjectSelection, Specialty

@login_required
def home(request):
    context = {
        "executors_count": Executor.objects.count(),
        "projects_count": Project.objects.count(),
        "selections_count": ProjectSelection.objects.count(),
        "specialties_count": Specialty.objects.count(),
    }

    return render(request, "directory/home.html", context)

def format_money(value):
    if value is None:
        return None
    return f"{value:,}".replace(",", " ")


@login_required
def executor_search(request):
    specialties = Specialty.objects.filter(is_active=True).order_by("code")

    selected_specialty_id = request.GET.get("specialty")
    show_all = request.GET.get("show_all") == "1"

    selected_specialty = None
    result_items = []

    if selected_specialty_id:
        selected_specialty = Specialty.objects.filter(id=selected_specialty_id).first()

        if selected_specialty:
            executors = (
                Executor.objects
                .filter(executor_specialties__specialty=selected_specialty)
                .select_related("status", "employment_type")
                .prefetch_related(
                    "executor_specialties__specialty",
                    "project_selections__project",
                    "project_selections__specialty",
                    "project_selections__status",
                    "comments",
                )
                .distinct()
            )

            if not show_all:
                executors = executors.filter(status__name="Активный")

            for executor in executors:
                specialties_text = ", ".join(
                    item.specialty.code
                    for item in executor.executor_specialties.all()
                )

                selections = [
                    selection
                    for selection in executor.project_selections.all()
                    if selection.specialty_id == selected_specialty.id
                ]

                selections = sorted(
                    selections,
                    key=lambda item: item.updated_at,
                    reverse=True,
                )

                offers = [
                    {
                        "amount": format_money(selection.offer_amount),
                        "selection": selection,
                    }
                    for selection in selections
                    if selection.offer_amount is not None
                ][:5]

                projects = []
                seen_project_ids = set()

                for selection in selections:
                    if selection.project_id not in seen_project_ids:
                        projects.append(selection.project.name)
                        seen_project_ids.add(selection.project_id)

                    if len(projects) >= 5:
                        break

                last_comment = executor.comments.all().order_by("-created_at").first()

                result_items.append(
                    {
                        "executor": executor,
                        "specialties": specialties_text,
                        "offers": offers,
                        "projects": projects,
                        "last_comment": last_comment,
                    }
                )

    context = {
        "specialties": specialties,
        "selected_specialty_id": selected_specialty_id,
        "selected_specialty": selected_specialty,
        "show_all": show_all,
        "executors": result_items,
    }

    return render(request, "directory/executor_search.html", context)