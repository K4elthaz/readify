from asgiref.sync import sync_to_async
from django.db.models import Q, Case, When, F
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from app.authentication.models import User
from app.chat.models import Message


@sync_to_async
def search_receiver(request):
    search = request.GET.get("search", "")
    user = request.user
    if search:
        users = User.objects.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(username__icontains=search)
            | Q(email__icontains=search),
        ).exclude(
            id=user.id
        )  # Exclude the current user
        return render(
            request,
            "search/search_receiver.html",
            {"users": users},
        )
    else:
        return render(
            request,
            "search/search_receiver.html",
            {"users": []},
        )


def view_message_details(request, pk):
    response = JsonResponse({"message": "Account type selected"})

    response["HX-Redirect"] = f"/message/{pk}/"
    return response


@sync_to_async
def send_message(request, pk):
    other_user = get_object_or_404(User, id=pk)
    # Retrieve the chat messages between the current user and the other user
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user)
        | Q(sender=other_user, receiver=request.user)
    ).order_by(
        "timestamp"
    )  # Order by timestamp to show oldest first

    inbox = (
        Message.objects.filter(Q(sender=request.user) | Q(receiver=request.user))
        .annotate(
            other_user=Case(
                When(sender=request.user, then=F("receiver")),
                When(receiver=request.user, then=F("sender")),
            )
        )
        .order_by("other_user", "-timestamp")
        .distinct("other_user")
    )
    inbox.update(mark_as_read=True)
    distinct_receivers = Message.objects.filter(sender=request.user).distinct(
        "receiver"
    )

    return render(
        request,
        "message_details.html",
        {
            "other_user": other_user,
            "messages": messages,
            "inbox": inbox,
            "messages_active": True,
            "total_distinct_receivers": distinct_receivers.count(),
        },
    )
