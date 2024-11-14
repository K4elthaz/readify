from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from app.social_newsfeed.models import SocialPost


class SocialPostView(LoginRequiredMixin, ListView):
    template_name: str = "social_homepage.html"
    login_url: str = "/signin"
    model = SocialPost
    context_object_name: str = "posts"

    def get_queryset(self):
        queryset = super().get_queryset().order_by("-created_at")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["social_active"] = True
        return context
