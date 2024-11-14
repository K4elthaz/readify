from django.db import models

from app.authentication.models import User
from app.models import BaseModel


# Create your models here.


class SocialPost(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    caption = models.TextField()
    media = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        db_table = "social_posts"
        verbose_name = "Social Post"
        verbose_name_plural = "Social Posts"

    def __str__(self):
        return self.caption
