from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),

    # Исполнители
    path("search/", views.executor_search, name="executor_search"),
    path("executors/", views.executor_list, name="executor_list"),
    path("executors/add/", views.executor_create, name="executor_create"),
    path("executors/<int:executor_id>/", views.executor_detail, name="executor_detail"),
    path("executors/<int:executor_id>/edit/", views.executor_update, name="executor_update"),
    path("executors/<int:executor_id>/comments/add/", views.add_executor_comment, name="add_executor_comment"),

    # Проекты
    path("projects/", views.project_list, name="project_list"),
    path("projects/add/", views.project_create, name="project_create"),
    path("projects/<int:project_id>/", views.project_detail, name="project_detail"),
    path("projects/<int:project_id>/edit/", views.project_update, name="project_update"),
    path("project-specialty-needs/<int:need_id>/delete/", views.delete_project_specialty_need, name="delete_project_specialty_need"),

    # Строки подбора
    path("selections/<int:selection_id>/update/", views.update_project_selection, name="update_project_selection"),
    path("selections/<int:selection_id>/negotiations/add/", views.add_selection_negotiation, name="add_selection_negotiation"),
    path("selections/<int:selection_id>/delete/", views.delete_project_selection, name="delete_project_selection"),
    path("negotiations/<int:negotiation_id>/delete/", views.delete_selection_negotiation, name="delete_selection_negotiation"),
]