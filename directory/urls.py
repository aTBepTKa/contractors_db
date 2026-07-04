from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.executor_search, name="executor_search"),
    path("executors/", views.executor_list, name="executor_list"),
    path("executors/add/", views.executor_create, name="executor_create"),
    path("executors/<int:executor_id>/", views.executor_detail, name="executor_detail"),
    path("projects/", views.project_list, name="project_list"),
    path("projects/<int:project_id>/", views.project_detail, name="project_detail"),
    path("selections/<int:selection_id>/update/", views.update_project_selection, name="update_project_selection"),
    path("selections/<int:selection_id>/negotiations/add/", views.add_selection_negotiation, name="add_selection_negotiation"),
    path("selections/<int:selection_id>/delete/", views.delete_project_selection, name="delete_project_selection"),
    path("executors/<int:executor_id>/comments/add/", views.add_executor_comment, name="add_executor_comment"),
]