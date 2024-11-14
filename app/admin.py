from collections import Counter

from django.contrib import admin
from django.contrib.admin import AdminSite, site
from django.db.models import Count
from django.template.response import TemplateResponse
from django.urls import path
from django.views.generic import TemplateView
from django_celery_results.admin import TaskResult, GroupResult
from unfold.admin import ModelAdmin
from unfold.views import UnfoldModelAdminViewMixin

from app.authentication.models import User
from app.models import BaseModel, Analytics

# Register your models here.
# Unregister the Groups model
admin.site.unregister(TaskResult)
admin.site.unregister(GroupResult)


class MyClassBasedView(UnfoldModelAdminViewMixin, TemplateView):
    title = "Analytics Dashboard"  # required: custom page header title
    permission_required = ()  # required: tuple of permissions
    template_name = "admin/analytics_dashboard.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the existing context
        context = super().get_context_data(**kwargs)
        age_analytics = (
            User.objects.values("age")
            .annotate(user_count=Count("id"))
            .filter(age__gte=0)
        )

        # Initialize a Counter to keep track of book preferences
        preference_counter = Counter()

        # Get all users with the 'onboarding' field populated
        users = User.objects.exclude(onboarding__isnull=True)

        # Loop through all users to get their 'book_preferences' and count them
        for user in users:
            # Extract the 'book_preferences' list directly from the onboarding field
            book_preferences = (
                user.onboarding[0].get("book_preferences", [])
                if user.onboarding
                else []
            )

            # Ensure the field is actually a list before proceeding
            if isinstance(book_preferences, list):
                preference_counter.update(book_preferences)

        preferences = [
            {"preference": key, "total_preferred": value}
            for key, value in preference_counter.items()
        ]

        print(preferences)
        context["age_analytics"] = list(age_analytics)
        context["preference_counter"] = preferences
        return context


@admin.register(Analytics)
class CustomAdmin(ModelAdmin):
    def get_urls(self):
        return super().get_urls() + [
            path(
                "dashboard",
                MyClassBasedView.as_view(model_admin=self),
                name="custom_name",
            ),
        ]


def list_admin_path_names(request):
    """
    View function to list all the path names used in the Django admin.
    """
    path_names = []
    for model_admin in site._registry.values():
        for pattern in model_admin.get_urls():
            path_names.append(pattern.name)

    print(path_names)
