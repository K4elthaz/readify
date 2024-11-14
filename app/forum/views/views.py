from typing import Dict, Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Count, F, Value, Prefetch
from django.db.models.functions import Concat
from django.views.generic import ListView, DetailView

from app.authentication.models import User
from app.forum.models import Topic, Community, CommunityMembers
from app.forum.views.services import get_comments_per_post_service


class ForumsView(LoginRequiredMixin, ListView):
    template_name: str = "forums_homepage.html"
    login_url: str = "/signin"
    context_object_name: str = "topics"

    def get_queryset(self) -> Dict[str, Any]:
        topics: Topic = Topic.objects.all().order_by("-created_at")

        queryset: Dict[str, Any] = {
            "topics": topics,
        }

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["forums_active"] = True
        return context


class ExploreCommunitiesView(LoginRequiredMixin, ListView):
    template_name: str = "forums_explore_communities.html"
    login_url: str = "/signin"
    context_object_name: str = "communities"
    model = Community

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # Filter communities where the current user is not a member
        communities = queryset.prefetch_related("members_community").exclude(
            members_community__member=user
        )

        result = [
            {
                "id": community.id,
                "name": community.name,
                "description": community.description,
                "total_members": community.members_community.all().count(),
                "initials": community.name[0].upper(),
                "slug": community.slug,
            }
            for community in communities
        ]

        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current"] = "Forums"
        context["current_page"] = "Explore"
        context["forums_active"] = True
        return context


class CommunityDetailView(LoginRequiredMixin, DetailView):
    template_name = "forums_community_detail_view.html"
    login_url = "/signin"
    context_object_name = "community"  # More appropriate context object name
    model = Community

    def get_queryset(self):
        queryset = super().get_queryset()
        community_slug = self.kwargs.get("slug")

        # Prepare the prefetch query with ordering
        topic_prefetch = Prefetch(
            "community_topic", queryset=Topic.objects.order_by("-created_at")
        )

        # Filter the queryset based on the community slug and apply the prefetch
        community_qs = queryset.filter(slug=community_slug).prefetch_related(
            topic_prefetch
        )

        return community_qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        initials = [com_qs.name[0] for com_qs in qs]
        community = self.get_object()
        current_user = self.request.user

        top_posters = (
            User.objects.filter(topic_author__community=community)
            .annotate(
                topic_count=Count("topic_author"),
                author_name=Concat(
                    F("first_name"),
                    Value(" "),
                    F("last_name"),
                    output_field=models.CharField(),
                ),
                author_profile_picture=F("profile_picture"),
                author_role=F("user_role"),
            )
            .order_by("-topic_count")[:10]
        )

        is_already_joined = CommunityMembers.objects.filter(
            community=community, member=current_user
        ).exists()

        context["top_posters"] = top_posters
        context["is_already_joined"] = is_already_joined

        context["initials"] = initials[0]
        context["current_slug"] = self.kwargs.get("slug")
        context["forums_active"] = True
        return context


class TopicDetailView(LoginRequiredMixin, DetailView):
    template_name = "forums_detail_view.html"
    login_url = "/signin"
    context_object_name = "topic"  # More appropriate context object name
    model = Topic

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.prefetch_related("topic_comment")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slug = self.kwargs.get("slug")
        topic: Topic = Topic.objects.get(slug=slug)

        comments = get_comments_per_post_service(slug)
        context["current"] = "Forums"
        context["current_page"] = "Newsfeed"
        context["comments_count"] = topic.total_comments()
        context["comments"] = comments
        context["slug"] = slug
        context["forums_active"] = True
        return context
