from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import get_object_or_404, render

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

@login_required
def executor_list(request):
    show_all = request.GET.get("show_all") == "1"
    specialty_id = request.GET.get("specialty")
    search_query = request.GET.get("q", "").strip()

    executors = (
        Executor.objects
        .select_related("status", "employment_type")
        .prefetch_related(
            "executor_specialties__specialty",
            "project_selections__project",
            "project_selections__specialty",
            "project_selections__status",
            "comments",
        )
        .order_by("last_name", "first_name", "middle_name")
    )

    if not show_all:
        executors = executors.filter(status__name="Активный")

    selected_specialty = None

    if specialty_id:
        selected_specialty = Specialty.objects.filter(id=specialty_id).first()

        if selected_specialty:
            executors = executors.filter(
                executor_specialties__specialty=selected_specialty
            )

    if search_query:
        executors = executors.filter(
            models.Q(last_name__icontains=search_query)
            | models.Q(first_name__icontains=search_query)
            | models.Q(middle_name__icontains=search_query)
            | models.Q(phone__icontains=search_query)
            | models.Q(email__icontains=search_query)
            | models.Q(messenger__icontains=search_query)
            | models.Q(general_comment__icontains=search_query)
        )

    executors = executors.distinct()

    result_items = []

    for executor in executors:
        specialties_text = ", ".join(
            item.specialty.code
            for item in executor.executor_specialties.all()
        )

        selections = sorted(
            executor.project_selections.all(),
            key=lambda item: item.updated_at,
            reverse=True,
        )

        last_projects = []
        seen_project_ids = set()

        for selection in selections:
            if selection.project_id not in seen_project_ids:
                last_projects.append(selection.project.name)
                seen_project_ids.add(selection.project_id)

            if len(last_projects) >= 3:
                break

        last_comment = executor.comments.all().order_by("-created_at").first()

        result_items.append(
            {
                "executor": executor,
                "specialties": specialties_text,
                "last_projects": last_projects,
                "last_comment": last_comment,
            }
        )

    context = {
        "items": result_items,
        "specialties": Specialty.objects.filter(is_active=True).order_by("code"),
        "selected_specialty_id": specialty_id,
        "selected_specialty": selected_specialty,
        "show_all": show_all,
        "search_query": search_query,
    }

    return render(request, "directory/executor_list.html", context)

@login_required
def executor_detail(request, executor_id):
    executor = get_object_or_404(
        Executor.objects
        .select_related("status", "employment_type")
        .prefetch_related(
            "executor_specialties__specialty",
            "comments__project",
            "comments__user",
            "project_selections__project",
            "project_selections__specialty",
            "project_selections__status",
            "project_selections__negotiations",
        ),
        id=executor_id,
    )

    specialties = [
        item.specialty
        for item in executor.executor_specialties.all()
    ]

    comments = executor.comments.all().order_by("-created_at")

    selections = sorted(
        executor.project_selections.all(),
        key=lambda item: item.updated_at,
        reverse=True,
    )

    selection_items = []

    for selection in selections:
        negotiations = selection.negotiations.all().order_by("-event_date", "-created_at")

        selection_items.append(
            {
                "selection": selection,
                "offer_amount": format_money(selection.offer_amount),
                "negotiations": negotiations,
            }
        )

    context = {
        "executor": executor,
        "specialties": specialties,
        "comments": comments,
        "selection_items": selection_items,
    }

    return render(request, "directory/executor_detail.html", context)