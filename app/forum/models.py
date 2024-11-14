from django.db import models
from autoslug import AutoSlugField

from app.authentication.models import User
from app.models import BaseModel


# Create your models here.
class Community(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    slug = AutoSlugField(populate_from="name")

    class Meta:
        db_table = "community"
        verbose_name = "Community"
        verbose_name_plural = "Communities"

    def __str__(self):
        return self.name


class CommunityMembers(BaseModel):
    community = models.ForeignKey(
        Community, on_delete=models.CASCADE, related_name="members_community"
    )
    member = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="community_members"
    )

    class Meta:
        db_table = "community_members"
        verbose_name = "Community Member"
        verbose_name_plural = "Communities Members"

    def __str__(self):
        return f"{self.community.name} Members"


class Topic(BaseModel):
    title = models.CharField(max_length=255)
    body = models.TextField()

    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="topic_author"
    )
    community = models.ForeignKey(
        Community, on_delete=models.CASCADE, related_name="community_topic"
    )

    slug = AutoSlugField(populate_from="title")

    class Meta:
        db_table = "topic"
        verbose_name = "Topic"
        verbose_name_plural = "Topics"

    def __str__(self):
        return self.title

    def total_comments(self):
        return TopicComments.objects.filter(topic=self).count()


class TopicComments(BaseModel):
    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="topic_comment"
    )
    comment_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="topic_commented_by"
    )
    comment = models.TextField()

    class Meta:
        db_table = "topic_comments"
        verbose_name = "Topic Comment"
        verbose_name_plural = "Topics Comments"

    def __str__(self):
        return f"{self.topic.title} - {self.comment_by} - {self.comment}"


class TopicCommentReply(BaseModel):
    comment = models.ForeignKey(
        TopicComments, on_delete=models.CASCADE, related_name="reply_comment"
    )
    reply_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="topic_comment_reply_by"
    )
    reply = models.TextField()

    class Meta:
        db_table = "topic_comment_reply"
        verbose_name = "Topic Comment Reply"
        verbose_name_plural = "Topics Comment Replies"

    def __str__(self):
        return f"{self.reply}"
