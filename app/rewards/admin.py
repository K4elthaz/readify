from django.contrib import admin
from unfold.admin import ModelAdmin

from app.rewards.models import Rewards


# Register your models here.
@admin.register(Rewards)
class RewardsAdmin(ModelAdmin):
    pass
