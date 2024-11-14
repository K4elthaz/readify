from django.urls import path

from app.rewards.views.services import (
    get_coins_service,
    claim_daily_reward,
    show_daily_rewards_modal,
    show_success_creating__post_today_service,
    claim_rewards_service,
    show_success_posting_in_forums_today_service,
    pay_using_rewards_coins_service,
)

# service_urlpatterns = [path("rewards", get_coins_service, name="get_coins_service")]

urlpatterns = [
    path("rewards/notif", get_coins_service, name="get_coins_service"),
    path(
        "rewards/daily/claim/<int:count>", claim_daily_reward, name="claim_daily_reward"
    ),
    path("rewards/daily", show_daily_rewards_modal, name="show_daily_rewards_modal"),
    path(
        "rewards/social-newsfeed",
        show_success_creating__post_today_service,
        name="show_success_creating__post_today_service",
    ),
    path(
        "rewards/claims/<str:reward_type>",
        claim_rewards_service,
        name="claim_rewards_service",
    ),
    path(
        "rewards/forums",
        show_success_posting_in_forums_today_service,
        name="show_success_posting_in_forums_today_service",
    ),
    path(
        "rewards/pay/unlock-chapter/<str:chapter_id>",
        pay_using_rewards_coins_service,
        name="pay_using_rewards_coins_service",
    ),
]
