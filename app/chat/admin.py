from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Message


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    pass