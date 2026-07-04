from django.urls import path

from . import views

urlpatterns = [
    path("search/", views.executor_search, name="executor_search"),
]