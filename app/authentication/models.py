from django.db import models

# Create your models here.
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from app.enums import RoleTypeEnum, GenderEnum
from app.models import BaseModel


# Create your models here.


class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, password, **extra_fields)


class User(AbstractUser, BaseModel):

    user_role = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)

    username = models.CharField(max_length=255, unique=True)

    email = models.CharField(max_length=255, unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    age = models.IntegerField(default=0, blank=True, null=True)
    birthday = models.DateField(auto_now_add=False, blank=True, null=True)
    profile_picture = models.CharField(max_length=255, blank=True, null=True)

    is_verified = models.BooleanField(default=False)

    onboarding = models.JSONField(default=dict, blank=True, null=True)

    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = CustomUserManager()

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class FollowedAuthor(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="followers")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followed_author"
    )
    followed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} follows {self.author.full_name}"
