from django.db import models

from app.authentication.models import User
from app.models import BaseModel


# Create your models here.
class Notifications(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="users_notifications"
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.full_name} - {self.message[:20]}"

    class Meta:
        ordering = ["-created_at"]
        db_table = "notifications"
        verbose_name = "Notifications"
        verbose_name_plural = "Notifications"
