from typing import Dict, List, Any

from asgiref.sync import sync_to_async
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils.html import format_html

from app.forum.models import (
    Community,
    CommunityMembers,
    Topic,
    TopicComments,
    TopicCommentReply,
)
from app.notifications.views.services import save_notifications
from app.utils import natural_time


@sync_to_async
def save_new_topic_service(request, slug):

    try:
        user = request.user
        title = request.POST.get("title", "")
        body = request.POST.get("body", "")

        community = Community.objects.get(slug=slug)
        Topic.objects.create(
            title=title,
            body=body,
            author=user,
            community_id=community.id,
        )
        response = JsonResponse({"message": "New Communtity post"})
        response["HX-Redirect"] = f"/forums/community/{slug}"
        return response
    except Exception as e:
        return render(
            request,
            "components/error_message_alert.html",
            {"message": str(e)},
        )


@sync_to_async
def add_new_community_service(request):
    if request.method == "POST":
        title = request.POST.get("title", "")
        description = request.POST.get("description", "")
        try:
            new_community = Community.objects.create(
                name=title, description=description
            )
            CommunityMembers.objects.create(
                community=new_community, member=request.user
            )
            response = JsonResponse({"message": "New Communtity created successfully"})
            response["HX-Redirect"] = f"/forums/explore"
            return response
        except Exception as ex:
            return render(
                request,
                "components/error_message_alert.html",
                {"message": str(ex)},
            )


@sync_to_async
def get_communities_service(request):
    user = request.user
    community = CommunityMembers.objects.filter(member=user)

    # Create the list of HTML strings
    community_list = [
        f"""
        <li>
            <!-- Current: "bg-gray-50 text-pink-600", Default: "text-gray-700 hover:text-pink-600 hover:bg-gray-50" -->
            <a hx-get="/forums/community/{com.community.slug}" hx-push-url="true" hx-target="body" method="get"
               class="cursor-pointer group flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6 text-gray-700 hover:bg-gray-50 hover:text-pink-600">
                <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg bg-white text-[0.625rem] font-medium text-gray-400 group-hover:border-pink-600 group-hover:text-pink-600">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-6">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 8.25 21 12m0 0-3.75 3.75M21 12H3" />
                    </svg>
                </span>
                <span class="truncate">{com.community.name}</span>
            </a>
        </li>
        """
        for com in community
    ]

    # Join all the HTML strings into one response
    response_html = "".join(community_list)

    # Use format_html for safe HTML rendering
    return HttpResponse(format_html(response_html))


def get_comments_per_post_service(topic_slug):
    try:
        topic: Topic = (
            Topic.objects.select_related("author", "community")
            .prefetch_related(
                "topic_comment__comment_by", "topic_comment__reply_comment__reply_by"
            )
            .get(slug=topic_slug)
        )

        comments = topic.topic_comment.all().order_by("-created_at")
        result: List[Dict[str, Any]] = [
            {
                "id": comment.id,
                "comment_by": comment.comment_by.get_full_name(),  # Assuming get_full_name() returns a string
                "comment_by_prof_pic": comment.comment_by.profile_picture,
                "created_at": natural_time(comment.created_at),
                "comment": comment.comment,
                "slug": comment.topic.slug,
                "replies": [
                    {
                        "id": reply.id,
                        "reply_by": reply.reply_by.get_full_name(),  # Assuming get_full_name() returns a string
                        "reply_by_prof_pic": reply.reply_by.profile_picture,
                        "created_at": natural_time(reply.created_at),
                        "reply": reply.reply,
                    }
                    for reply in comment.reply_comment.all().order_by("-created_at")
                ],
            }
            for comment in comments
        ]
        return result

    except Topic.DoesNotExist:
        # Return an empty list if the topic does not exist
        return []

    except Exception as ex:
        # Re-raise any other exceptions for further handling
        raise ex


@sync_to_async
def add_comment_service(request, slug):
    if request.method == "POST":
        user = request.user
        comment = request.POST.get("comment", "")
        topic: Topic = Topic.objects.filter(slug=slug).first()
        comment = TopicComments.objects.create(
            comment_by=user, topic_id=topic.id, comment=comment
        )

        notification_message = f"""
            <p class="text-sm font-semibold text-gray-900">You have a new comment on your post!</p>
            <hr>
            <p class="mt-2 text-xs text-gray-500">
                <span class="font-semibold text-gray-900">{user.full_name()}</span> commented on your post.
                You can view the comment <a href="/forums/community/topic/{topic.slug}" class="text-pink-500 underline">here</a>.
            </p>
        """
        save_notifications(user=topic.author, message=notification_message)

        response = JsonResponse({"message": "New comment created successfully"})
        response["HX-Redirect"] = f"/forums/community/topic/{slug}"
        return response


@sync_to_async
def add_reply_to_comment_service(request, slug, comment_id):
    if request.method == "POST":
        user = request.user
        reply = request.POST.get("reply", "")
        comment = TopicComments.objects.filter(id=comment_id).first()
        TopicCommentReply.objects.create(
            comment_id=comment_id, reply_by=user, reply=reply
        )

        if comment.comment_by != user:
            notification_message = f"""
                <p class="text-sm font-semibold text-gray-900">You have a new reply to your comment!</p>
                <hr>
                <p class="mt-2 text-xs text-gray-500">
                    <span class="font-semibold text-gray-900">{user.full_name()}</span> replied to your comment.
                    You can view the reply <a href="/forums/community/topic/{comment.topic.slug}" class="text-pink-500 underline">here</a>.
                </p>
            """
            save_notifications(user=comment.comment_by, message=notification_message)
        response = JsonResponse({"message": "Reply to a comment created successfully"})
        response["HX-Redirect"] = f"/forums/community/topic/{slug}"
        return response


@sync_to_async
def join_community_service(request, slug):
    user = request.user
    community = Community.objects.filter(slug=slug).first()
    CommunityMembers.objects.create(community=community, member=user)

    response = JsonResponse({"message": "Join in community successfully"})
    response["HX-Redirect"] = f"/forums/community/{slug}"
    return response


@sync_to_async
def search_forums_service(request):
    user = request.user
    query = request.GET.get("search", False)

    if query:

        forums_queryset = (
            Community.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
            .prefetch_related("members_community")
            .exclude(members_community__member=user)
        )

        if forums_queryset:

            result = [
                {
                    "id": community.id,
                    "name": community.name,
                    "description": community.description,
                    "total_members": community.members_community.all().count(),
                    "initials": community.name[0].upper(),
                    "slug": community.slug,
                }
                for community in forums_queryset
            ]
            return render(
                request,
                "search/search_forums.html",
                {"communities": result},
            )
        else:
            return HttpResponse(
                """
                <main class="grid min-h-full place-items-center bg-white px-6 py-24 sm:py-32 lg:px-8">
                  <div class="text-center">
                    <p class="text-base font-semibold text-pink-600">404</p>
                    <h1 class="mt-4 text-3xl font-bold tracking-tight text-gray-900 sm:text-5xl">Search result not found</h1>
                    <p class="mt-6 text-base leading-7 text-gray-600">Sorry, we couldn’t find what you’re looking for.</p>
                    <div class="mt-10 flex items-center justify-center gap-x-6">
                    </div>
                  </div>
                </main>
            """
            )
    else:
        response = JsonResponse({"message": "Search empty"})
        response["HX-Redirect"] = f"/forums/explore"
        return response
