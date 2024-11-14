import json
import random
import string
from typing import List, Any

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from cloudinary import CloudinaryImage

from app.authentication.models import User
from app.books.models import BooksChapter
from app.chat.models import Message
from app.notifications.models import Notifications
from app.notifications.views.services import save_notifications
from app.utils import UploadFilesToCloudinary


class CollaborationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.content_slug = self.scope["url_route"]["kwargs"]["slug"]
        self.room_name = f"content_{self.content_slug}"
        self.room_group_name = f"group_{self.room_name}"

        # Join the room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Fetch and send initial content
        content = await self.get_content()
        await self.send(
            text_data=json.dumps({"type": "initial_content", "content": content})
        )

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get("content", "")

        # Save the content to the database
        await self.save_content(content)

        # Broadcast the content to the group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "collaborate_message", "content": content}
        )

    async def collaborate_message(self, event):
        content = event["content"]
        # Send the message to the WebSocket
        await self.send(
            text_data=json.dumps({"type": "content_update", "content": content})
        )

    @database_sync_to_async
    def get_content(self):
        content = BooksChapter.objects.get(slug=self.content_slug)
        return content.content

    @database_sync_to_async
    def save_content(self, content):
        BooksChapter.objects.filter(slug=self.content_slug).update(content=content)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # The room will be the combination of both user IDs (sorted to ensure uniqueness)
        self.user = self.scope["user"]
        self.other_user = self.scope["url_route"]["kwargs"]["pk"]
        self.room_name = (
            f"chat_{'_'.join(sorted([str(self.user.pk), self.other_user]))}"
        )

        self.room_group_name = f"chat_{self.room_name}"

        # Join the private chat room (group)
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        file = data.get("file", None)

        image_url: str | None = None

        if file:
            res = "".join(random.choices(string.ascii_letters, k=14))
            folder: str = "chat_images"
            file_name: str = f"{folder}/{res}/sent-by={self.user.email}/{res}"

            init_cloudinary: UploadFilesToCloudinary = UploadFilesToCloudinary()
            transformation: List[dict[str, Any]] = [{"width": 1000, "height": 1000}]
            init_cloudinary.upload_file(
                file,
                public_id=file_name,
                transformation=transformation,
            )
            image_url = CloudinaryImage(file_name).build_url()

        # Send message to the room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": self.user.email,
                "image_url": image_url,
            },
        )

        # Save the message to the database
        receiver = await sync_to_async(User.objects.get)(id=self.other_user)
        notification_message = f"""<p class="text-sm font-semibold text-gray-900">New message received!</p>
               <hr>
               <p class="mt-2 text-xs text-gray-500">
                   <span class="font-semibold text-gray-900">{self.user.full_name()}</span> sent you a message. 
                   View it <a href="/message/{self.user.id}/" class="text-pink-500 underline">here</a>
               </p>
           """
        await self.save_notifications(user=receiver, message=notification_message)
        await self.save_message(self.user, receiver, message, image_url)

    # Receive message from the room group
    async def chat_message(self, event):
        message = event["message"]
        sender = event["sender"]

        # Send message to WebSocket
        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "image_url": event["image_url"],
                    "sender": sender,
                    "profile_picture": self.user.profile_picture,
                    "full_name": self.user.full_name(),
                }
            )
        )

    @sync_to_async
    def save_message(self, sender, receiver, message, image_url):
        Message.objects.create(
            sender=sender,
            receiver=receiver,
            message=message,
            image_attachment_url=image_url,
        )

    @sync_to_async
    def save_notifications(self, user, message):
        Notifications.objects.create(user=user, message=message)
