from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ExecutorForm, ProjectForm
from .models import (
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
    return redirect("executor_list")

@login_required
def executor_list(request):
    show_all = request.GET.get("show_all") == "1"
    specialty_id = request.GET.get("specialty")
    status_id = request.GET.get("status")
    revit_filter = request.GET.get("revit")
    search_query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "name")

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

    selected_status = None

    if status_id:
        selected_status = SelectionStatus.objects.filter(id=status_id).first()

    # Здесь нужен именно статус исполнителя, а не статус подбора.
    executor_statuses = ExecutorStatus.objects.filter(is_active=True).order_by("name")

    if status_id:
        executors = executors.filter(status_id=status_id)

    if revit_filter == "yes":
        executors = executors.filter(works_in_revit=True)
    elif revit_filter == "no":
        executors = executors.filter(works_in_revit=False)

    if search_query:
        executors = executors.filter(
            models.Q(last_name__icontains=search_query)
            | models.Q(first_name__icontains=search_query)
            | models.Q(middle_name__icontains=search_query)
            | models.Q(phone__icontains=search_query)
            | models.Q(email__icontains=search_query)
            | models.Q(messenger__icontains=search_query)
            | models.Q(general_comment__icontains=search_query)
            | models.Q(status_comment__icontains=search_query)
            | models.Q(revit_comment__icontains=search_query)
        )

    if sort == "status":
        executors = executors.order_by("status__name", "last_name", "first_name")
    elif sort == "revit":
        executors = executors.order_by("-works_in_revit", "last_name", "first_name")
    else:
        executors = executors.order_by("last_name", "first_name", "middle_name")

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
                last_projects.append(
                    {
                        "project": selection.project.name,
                        "specialty": selection.specialty.code,
                        "amount": format_money(selection.offer_amount),
                    }
                )
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
        "executor_statuses": executor_statuses,
        "selected_specialty_id": specialty_id,
        "selected_specialty": selected_specialty,
        "selected_status_id": status_id,
        "show_all": show_all,
        "search_query": search_query,
        "revit_filter": revit_filter,
        "sort": sort,
        "total_executors_count": Executor.objects.count(),
        "active_executors_count": Executor.objects.filter(status__name="Активный").count(),
        "inactive_executors_count": Executor.objects.exclude(status__name="Активный").count(),
        "revit_executors_count": Executor.objects.filter(works_in_revit=True).count(),
    }

    return render(request, "directory/executor_list.html", context)
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
        "total_executors_count": Executor.objects.count(),
        "active_executors_count": Executor.objects.filter(status__name="Активный").count(),
        "inactive_executors_count": Executor.objects.exclude(status__name="Активный").count(),
        "revit_executors_count": Executor.objects.filter(works_in_revit=True).count(),
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
            "project_selections__project__object_type",
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

    used_specialty_ids = [
        item.specialty_id
        for item in executor.executor_specialties.all()
    ]

    available_specialties = Specialty.objects.filter(
        is_active=True
    ).exclude(
        id__in=used_specialty_ids
    ).order_by("code")

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
        "projects": Project.objects.order_by("name"),
        "executor_specialties": executor.executor_specialties.all(),
        "available_specialties": available_specialties,
    }

    return render(request, "directory/executor_detail.html", context)

@login_required
def project_list(request):
    search_query = request.GET.get("q", "").strip()
    object_type_id = request.GET.get("object_type")

    projects = (
        Project.objects
        .select_related("object_type")
        .prefetch_related(
            "selections__specialty",
            "selections__executor",
            "selections__status",
        )
        .order_by("name")
    )

    selected_object_type = None

    if object_type_id:
        selected_object_type = ObjectType.objects.filter(id=object_type_id).first()

        if selected_object_type:
            projects = projects.filter(object_type=selected_object_type)

    if search_query:
        projects = projects.filter(
            models.Q(name__icontains=search_query)
            | models.Q(comment__icontains=search_query)
        )

    result_items = []

    for project in projects:
        selections = project.selections.all()

        total_offer_amount = sum(
            selection.offer_amount or 0
            for selection in selections
        )

        specialties = []
        seen_specialty_ids = set()

        for selection in selections:
            if selection.specialty_id not in seen_specialty_ids:
                specialties.append(selection.specialty.code)
                seen_specialty_ids.add(selection.specialty_id)

        result_items.append(
            {
                "project": project,
                "selections_count": len(selections),
                "total_offer_amount": format_money(total_offer_amount),
                "specialties": ", ".join(specialties),
            }
        )

    context = {
        "items": result_items,
        "search_query": search_query,
        "object_types": ObjectType.objects.filter(is_active=True).order_by("name"),
        "selected_object_type_id": object_type_id,
        "selected_object_type": selected_object_type,
        "total_projects_count": Project.objects.count(),
        "total_selections_count": ProjectSelection.objects.count(),
    }

    return render(request, "directory/project_list.html", context)

@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)

        if form.is_valid():
            project = form.save()
            return redirect("project_detail", project_id=project.id)
    else:
        form = ProjectForm()

    context = {
        "form": form,
        "page_title": "Новый проект",
        "submit_text": "Создать проект",
        "back_url": "/projects/",
        "back_text": "← К списку проектов",
    }

    return render(request, "directory/project_form.html", context)

@login_required
def project_update(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("object_type"),
        id=project_id,
    )

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)

        if form.is_valid():
            project = form.save()
            return redirect("project_detail", project_id=project.id)
    else:
        form = ProjectForm(instance=project)

    context = {
        "form": form,
        "project": project,
        "page_title": f"Редактирование проекта: {project.name}",
        "submit_text": "Сохранить изменения",
        "back_url": f"/projects/{project.id}/",
        "back_text": "← К карточке проекта",
    }

    return render(request, "directory/project_form.html", context)

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(
        Project.objects
        .select_related("object_type")
        .prefetch_related(
            "selections__specialty",
            "selections__executor",
            "selections__executor__status",
            "selections__status",
            "selections__negotiations",
            "selections__negotiations__user",
        ),
        id=project_id,
    )

    add_candidate_error = None

    selected_specialty_id = request.GET.get("specialty")
    selected_specialty = None
    candidate_items = []

    selection_specialty_id = request.GET.get("selection_specialty")
    selection_status_id = request.GET.get("selection_status")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add_candidate":
            specialty_id = request.POST.get("specialty_id")
            executor_id = request.POST.get("executor_id")

            specialty = Specialty.objects.filter(id=specialty_id).first()
            executor = Executor.objects.filter(id=executor_id).first()
            new_status = SelectionStatus.objects.filter(name="Новый").first()

            if not new_status:
                add_candidate_error = (
                    "В справочнике статусов подбора нет статуса «Новый». "
                    "Добавьте его через админку."
                )
            elif not specialty or not executor:
                add_candidate_error = "Не выбрана специальность или исполнитель."
            else:
                try:
                    ProjectSelection.objects.create(
                        project=project,
                        specialty=specialty,
                        executor=executor,
                        status=new_status,
                    )
                    return redirect("project_detail", project_id=project.id)
                except IntegrityError:
                    add_candidate_error = (
                        "Этот исполнитель уже добавлен в проект по выбранной специальности."
                    )

            selected_specialty_id = specialty_id

        else:
            return redirect("project_detail", project_id=project.id)
    
    if selected_specialty_id:
        selected_specialty = Specialty.objects.filter(id=selected_specialty_id).first()

        if selected_specialty:
            used_executor_ids = ProjectSelection.objects.filter(
                project=project,
                specialty=selected_specialty,
            ).values_list("executor_id", flat=True)

            candidates = (
                Executor.objects
                .filter(
                    executor_specialties__specialty=selected_specialty,
                    status__name="Активный",
                )
                .exclude(id__in=used_executor_ids)
                .select_related("status", "employment_type")
                .prefetch_related(
                    "executor_specialties__specialty",
                    "project_selections__project",
                    "project_selections__specialty",
                    "project_selections__status",
                    "comments",
                )
                .distinct()
                .order_by("last_name", "first_name", "middle_name")
            )

            for candidate in candidates:
                candidate_selections = [
                    selection
                    for selection in candidate.project_selections.all()
                    if selection.specialty_id == selected_specialty.id
                ]

                candidate_selections = sorted(
                    candidate_selections,
                    key=lambda item: item.updated_at,
                    reverse=True,
                )

                offers = [
                    format_money(selection.offer_amount)
                    for selection in candidate_selections
                    if selection.offer_amount is not None
                ][:5]

                projects = []
                seen_project_ids = set()

                for selection in candidate_selections:
                    if selection.project_id not in seen_project_ids:
                        projects.append(selection.project.name)
                        seen_project_ids.add(selection.project_id)

                    if len(projects) >= 5:
                        break

                last_comment = candidate.comments.all().order_by("-created_at").first()

                candidate_items.append(
                    {
                        "executor": candidate,
                        "offers": offers,
                        "projects": projects,
                        "last_comment": last_comment,
                    }
                )

    selections = project.selections.all()

    if selection_specialty_id:
        selections = selections.filter(specialty_id=selection_specialty_id)

    if selection_status_id:
        selections = selections.filter(status_id=selection_status_id)

    selections = selections.order_by(
        "specialty__code",
        "offer_amount",
        "executor__last_name",
        "executor__first_name",
    )

    selection_items = []
    total_offer_amount = 0

    for selection in selections:
        if selection.offer_amount:
            total_offer_amount += selection.offer_amount

        negotiations = selection.negotiations.all().order_by(
            "-event_date",
            "-created_at",
        )

        selection_items.append(
            {
                "selection": selection,
                "offer_amount": format_money(selection.offer_amount),
                "negotiations": negotiations,
            }
        )

    context = {
        "project": project,
        "selection_items": selection_items,
        "selections_count": len(selection_items),
        "total_offer_amount": format_money(total_offer_amount),
        "add_candidate_error": add_candidate_error,
        "specialties": Specialty.objects.filter(is_active=True).order_by("code"),
        "selected_specialty_id": selected_specialty_id,
        "selected_specialty": selected_specialty,
        "candidate_items": candidate_items,
        "selection_statuses": SelectionStatus.objects.filter(is_active=True).order_by("name"),
        "selection_specialty_id": selection_specialty_id,
        "selection_status_id": selection_status_id,
    }

    return render(request, "directory/project_detail.html", context)

@login_required
def update_project_selection(request, selection_id):
    selection = get_object_or_404(
        ProjectSelection.objects.select_related("project"),
        id=selection_id,
    )

    if request.method != "POST":
        return redirect("project_detail", project_id=selection.project.id)

    status_id = request.POST.get("status")
    offer_amount_raw = request.POST.get("offer_amount", "").strip()
    comment = request.POST.get("comment", "").strip()

    status = SelectionStatus.objects.filter(id=status_id).first()

    if status:
        selection.status = status

    if offer_amount_raw:
        try:
            selection.offer_amount = int(offer_amount_raw.replace(" ", ""))
        except ValueError:
            pass
    else:
        selection.offer_amount = None

    selection.comment = comment
    selection.save()

    return redirect("project_detail", project_id=selection.project.id)

@login_required
def add_selection_negotiation(request, selection_id):
    selection = get_object_or_404(
        ProjectSelection.objects.select_related("project"),
        id=selection_id,
    )

    if request.method != "POST":
        return redirect("project_detail", project_id=selection.project.id)

    comment = request.POST.get("comment", "").strip()

    if comment:
        SelectionNegotiation.objects.create(
            selection=selection,
            event_date=timezone.localdate(),
            comment=comment,
            user=request.user,
        )

    return redirect("project_detail", project_id=selection.project.id)

@login_required
def delete_project_selection(request, selection_id):
    selection = get_object_or_404(
        ProjectSelection.objects.select_related("project"),
        id=selection_id,
    )

    project_id = selection.project.id

    if request.method == "POST":
        selection.delete()

    return redirect("project_detail", project_id=project_id)

@login_required
def add_executor_comment(request, executor_id):
    executor = get_object_or_404(Executor, id=executor_id)

    if request.method != "POST":
        return redirect("executor_detail", executor_id=executor.id)

    project_id = request.POST.get("project_id")
    comment_text = request.POST.get("comment", "").strip()

    project = None

    if project_id:
        project = Project.objects.filter(id=project_id).first()

    if comment_text:
        ExecutorComment.objects.create(
            executor=executor,
            project=project,
            user=request.user,
            comment=comment_text,
        )

    return redirect("executor_detail", executor_id=executor.id)

def update_executor_specialties(executor, specialties):
    specialties = specialties or []

    ExecutorSpecialty.objects.filter(executor=executor).exclude(
        specialty__in=specialties
    ).delete()

    for specialty in specialties:
        ExecutorSpecialty.objects.get_or_create(
            executor=executor,
            specialty=specialty,
        )

@login_required
def executor_create(request):
    if request.method == "POST":
        form = ExecutorForm(request.POST)

        if form.is_valid():
            executor = form.save()
            specialties = form.cleaned_data.get("specialties")
            update_executor_specialties(executor, specialties)

            return redirect("executor_detail", executor_id=executor.id)
    else:
        form = ExecutorForm()

    context = {
        "form": form,
        "page_title": "Новый исполнитель",
        "submit_text": "Создать исполнителя",
        "back_url": "/executors/",
        "back_text": "← К списку исполнителей",
    }

    return render(request, "directory/executor_form.html", context)

@login_required
def add_executor_specialty(request, executor_id):
    executor = get_object_or_404(Executor, id=executor_id)

    if request.method != "POST":
        return redirect("executor_detail", executor_id=executor.id)

    specialty_id = request.POST.get("specialty")
    specialty = Specialty.objects.filter(id=specialty_id, is_active=True).first()

    if specialty:
        ExecutorSpecialty.objects.get_or_create(
            executor=executor,
            specialty=specialty,
        )

    return redirect("executor_detail", executor_id=executor.id)


@login_required
def delete_executor_specialty(request, executor_specialty_id):
    executor_specialty = get_object_or_404(
        ExecutorSpecialty.objects.select_related("executor"),
        id=executor_specialty_id,
    )

    executor_id = executor_specialty.executor.id

    if request.method == "POST":
        executor_specialty.delete()

    return redirect("executor_detail", executor_id=executor_id)

@login_required
def executor_update(request, executor_id):
    executor = get_object_or_404(
        Executor.objects
        .select_related("status", "employment_type")
        .prefetch_related("executor_specialties__specialty"),
        id=executor_id,
    )

    selected_specialty_ids = list(
        executor.executor_specialties.values_list(
            "specialty_id",
            flat=True,
        )
    )

    if request.method == "POST":
        form = ExecutorForm(request.POST, instance=executor)

        if form.is_valid():
            executor = form.save()
            specialties = form.cleaned_data.get("specialties")
            update_executor_specialties(executor, specialties)

            return redirect("executor_detail", executor_id=executor.id)
    else:
        form = ExecutorForm(
            instance=executor,
            initial={
                "specialties": selected_specialty_ids,
            },
        )

    context = {
        "form": form,
        "executor": executor,
        "page_title": f"Редактирование: {executor}",
        "submit_text": "Сохранить изменения",
        "back_url": f"/executors/{executor.id}/",
        "back_text": "← К карточке исполнителя",
    }

    return render(request, "directory/executor_form.html", context)