from django.http import HttpResponse
from django.shortcuts import render

from app.notifications.models import Notifications


def save_notifications(user, message):
    Notifications.objects.create(user=user, message=message)


def get_notifications_service(request):
    notifications = Notifications.objects.filter(user=request.user).order_by(
        "-created_at"
    )
    return render(
        request,
        "components/notifications_lists.html",
        {"notifications": notifications},
    )


def mark_notifications_as_read_service(request, notification_id):
    Notifications.objects.filter(user=request.user, id=notification_id).update(
        is_read=True
    )
    return HttpResponse("")


def notifications_count_service(request):
    notifications = Notifications.objects.filter(
        user=request.user, is_read=False
    ).count()

    if notifications != 0:
        return HttpResponse(
            f"""<span class="absolute right-0 top-0 flex items-center justify-center h-5 w-5 rounded-full bg-red-500 ring-2 ring-white">
                    <p class="text-white text-xs font-bold leading-none">{notifications}</p>
                </span>
            """
        )
    return HttpResponse("")
