from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin


READ_ONLY_GROUP = "Только просмотр"
READ_VIEWS = {
    "home", "executor_search", "executor_list", "executor_detail",
    "project_list", "project_detail",
}


class ReadOnlyAccessMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = request.user
        # Superusers retain recovery access; the restrictive role wins over
        # all other groups and staff status for everyone else.
        request.read_only = (
            user.is_authenticated and not user.is_superuser
            and user.groups.filter(name=READ_ONLY_GROUP).exists()
        )

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.read_only:
            return None
        match = request.resolver_match
        is_directory = view_func.__module__.startswith("directory.")
        if match.app_name == "admin" or (
            is_directory and (
                request.method not in {"GET", "HEAD", "OPTIONS"}
                or match.url_name not in READ_VIEWS
            )
        ):
            return HttpResponseForbidden("Доступ только для просмотра. Изменение записей запрещено.")
        return None
