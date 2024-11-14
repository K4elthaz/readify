from django.urls import path

from app.chat.views.services import search_receiver, send_message, view_message_details
from app.chat.views.views import MessagesPageView


service_urlpatterns = [
    path("search/receiver", search_receiver, name="search_receiver"),
    path("message/<str:pk>/", send_message, name="send_message"),
    path("message/view/<str:pk>", view_message_details, name="view_message_details"),
]
urlpatterns = [
    path("messages", MessagesPageView.as_view(), name="messages"),
] + service_urlpatterns
