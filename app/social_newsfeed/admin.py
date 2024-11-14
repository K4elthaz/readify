from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import SocialPost


@admin.register(SocialPost)
class SocialPostAdmin(ModelAdmin):
    pass