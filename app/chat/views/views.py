from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, When, Case, F
from django.shortcuts import render
from django.views.generic import ListView

from app.chat.models import Message


# Create your views here.
class MessagesPageView(LoginRequiredMixin, ListView):
    template_name: str = "messages_view.html"
    login_url: str = "/signin"
    model = Message
    context_object_name: str = "messages"

    def get_queryset(self):
        user = self.request.user
        # Filter to get distinct receivers of messages sent by the current user
        queryset = (
            super()
            .get_queryset()
            .filter(Q(sender=self.request.user) | Q(receiver=self.request.user))
            .annotate(
                other_user=Case(
                    When(sender=user, then=F("receiver")),
                    When(receiver=user, then=F("sender")),
                )
            )
            .order_by("other_user", "-timestamp")
            .distinct("other_user")
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get distinct receivers for the messages
        distinct_receivers = (
            super().get_queryset().filter(sender=self.request.user).distinct("receiver")
        )
        context["messages_active"] = True
        context["total_distinct_receivers"] = distinct_receivers.count()

        return context
