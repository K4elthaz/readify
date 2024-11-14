from django.urls import path

from app.notifications.views.services import (
    get_notifications_service,
    mark_notifications_as_read_service,
    notifications_count_service,
)

urlpatterns = [
    path("notifications", get_notifications_service, name="get_notifications_service"),
    path(
        "notifications/count",
        notifications_count_service,
        name="notifications_count_service",
    ),
    path(
        "notifications/<str:notification_id>/",
        mark_notifications_as_read_service,
        name="mark_notifications_as_read_service",
    ),
]
