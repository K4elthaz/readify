from django.db import models

from app.authentication.models import User
from app.models import BaseModel


# Create your models here.
class Rewards(BaseModel):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coins = models.IntegerField(default=0)

    class Meta:
        db_table = "rewards"
        verbose_name = "Rewards"
        verbose_name_plural = "Rewards"

    def __str__(self):
        return f"{self.user.full_name()} | {self.coins} coins"


class ClaimedRewards(BaseModel):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reward_type = models.CharField(max_length=255)

    class Meta:
        db_table = "claimed_rewards"
        verbose_name = "Claimed Rewards"
        verbose_name_plural = "Claimed Rewards"

    def __str__(self):
        return f"{self.user.username} claimed {self.reward_type}"
