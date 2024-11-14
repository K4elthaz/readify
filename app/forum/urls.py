from django.urls import path

from app.forum.views.services import (
    add_new_community_service,
    get_communities_service,
    save_new_topic_service,
    add_comment_service,
    add_reply_to_comment_service,
    join_community_service,
    search_forums_service,
)
from app.forum.views.views import (
    ForumsView,
    ExploreCommunitiesView,
    CommunityDetailView,
    TopicDetailView,
)

service_urlpatterns = [
    path(
        "forums/community/add/",
        add_new_community_service,
        name="add_new_community_service",
    ),
    path(
        "forums/my-communities/",
        get_communities_service,
        name="get_communities_service",
    ),
    path(
        "forums/topic/new/<str:slug>",
        save_new_topic_service,
        name="save_new_topic_service",
    ),
    path(
        "forums/topic/comment/<str:slug>",
        add_comment_service,
        name="add_comment_service",
    ),
    path(
        "forums/topic/comment/reply/<str:slug>/<str:comment_id>",
        add_reply_to_comment_service,
        name="add_reply_to_comment_service",
    ),
    path(
        "forums/community/join/<str:slug>",
        join_community_service,
        name="join_community_service",
    ),
    path(
        "forums/search/",
        search_forums_service,
        name="search_forums_service",
    ),
]
urlpatterns = [
    path("forums/newsfeed", ForumsView.as_view(), name="forums_newsfeed"),
    path(
        "forums/explore",
        ExploreCommunitiesView.as_view(),
        name="explore_communities",
    ),
    path(
        "forums/community/<str:slug>",
        CommunityDetailView.as_view(),
        name="community_detail",
    ),
    path(
        "forums/community/topic/<str:slug>",
        TopicDetailView.as_view(),
        name="topic_detail",
    ),
] + service_urlpatterns
