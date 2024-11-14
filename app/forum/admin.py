from django.contrib import admin
from unfold.admin import ModelAdmin

from app.forum.models import (
    Community,
    CommunityMembers,
    Topic,
    TopicComments,
    TopicCommentReply,
)


@admin.register(Community)
class CommunityAdmin(ModelAdmin):
    pass


@admin.register(CommunityMembers)
class CommunityMembersAdmin(ModelAdmin):
    pass


@admin.register(Topic)
class TopicAdmin(ModelAdmin):
    pass


@admin.register(TopicComments)
class TopicCommentsAdmin(ModelAdmin):
    pass


@admin.register(TopicCommentReply)
class TopicCommentReplyAdmin(ModelAdmin):
    pass
