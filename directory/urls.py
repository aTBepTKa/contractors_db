from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.executor_search, name="executor_search"),
    path("executors/", views.executor_list, name="executor_list"),
    path("executors/<int:executor_id>/", views.executor_detail, name="executor_detail"),
    path("projects/", views.project_list, name="project_list"),
]