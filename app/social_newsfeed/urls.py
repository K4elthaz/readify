from django.urls import path

from app.social_newsfeed.views.services import new_post, delete_social_post_service
from app.social_newsfeed.views.views import SocialPostView


services_patterns = [
    path("social/post/new", new_post, name="new_post"),
    path(
        "social/post/delete/<str:id>",
        delete_social_post_service,
        name="delete_social_post_service",
    ),
]

urlpatterns = [
    path("social", SocialPostView.as_view(), name="social")
] + services_patterns
