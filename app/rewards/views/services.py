from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.html import format_html

from app.books.models import ChapterUnlockedByUser, BooksChapter
from app.enums import RewardType
from app.forum.models import Topic
from app.rewards.models import Rewards, ClaimedRewards
from app.social_newsfeed.models import SocialPost


def get_coins_service(request):

    user = request.user

    rewards = get_object_or_404(Rewards, user=user)

    # Use format_html for safe HTML rendering
    return HttpResponse(
        f"""
        <p class="text-sm font-semibold text-gray-900">{rewards.coins}</p>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor"
             class="size-5 text-yellow-500">
            <path fill-rule="evenodd"
                  d="M10 1c3.866 0 7 1.79 7 4s-3.134 4-7 4-7-1.79-7-4 3.134-4 7-4Zm5.694 8.13c.464-.264.91-.583 1.306-.952V10c0 2.21-3.134 4-7 4s-7-1.79-7-4V8.178c.396.37.842.688 1.306.953C5.838 10.006 7.854 10.5 10 10.5s4.162-.494 5.694-1.37ZM3 13.179V15c0 2.21 3.134 4 7 4s7-1.79 7-4v-1.822c-.396.37-.842.688-1.306.953-1.532.875-3.548 1.369-5.694 1.369s-4.162-.494-5.694-1.37A7.009 7.009 0 0 1 3 13.179Z"
                  clip-rule="evenodd"/>
        </svg>
        <svg onclick="showRewardHelp()" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-4 text-gray-500 cursor-pointer">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
        </svg>
        """
    )


def claim_daily_reward(request, count):
    user = request.user

    reward = Rewards.objects.filter(user=user).first()

    reward.coins += count
    reward.updated_at = timezone.now()
    reward.save()

    return render(request, "success_claim_daily_reward_modal.html")


def show_daily_rewards_modal(request):
    user = request.user
    today = timezone.now().date()

    rewards = Rewards.objects.filter(
        user=user,
        updated_at__date=today,
    )

    if not rewards:
        return render(request, "daily_reward_modal.html")
    else:
        return HttpResponse("")


def show_success_creating__post_today_service(request):
    user = request.user
    today = timezone.now().date()

    social_post = SocialPost.objects.filter(author=user, created_at__date=today)
    rewards = ClaimedRewards.objects.filter(
        user=user,
        reward_type="DAILY_20_SOCIAL_POST",
        created_at__date=today,
    )

    context = {
        "title": "Congratulations! You posted 20 times today!",
        "description": "Claim your reward to receive 10 coins!",
        "reward_type": "DAILY_20_SOCIAL_POST",
    }

    if social_post.count() >= 20 and not rewards:
        return render(request, "components/claim_rewards_modal.html", context)
    else:
        return HttpResponse("")


def claim_rewards_service(request, reward_type):
    user = request.user

    reward_type_enum = RewardType[reward_type]

    reward = Rewards.objects.filter(user=user).first()

    reward.coins += reward_type_enum.value
    reward.updated_at = timezone.now()
    reward.save()

    ClaimedRewards.objects.create(user=user, reward_type=reward_type)
    response = JsonResponse({"message": "Claiming your rewards"})

    if reward_type == "DAILY_20_SOCIAL_POST":
        response["HX-Redirect"] = f"/social"
    elif reward_type == "DAILY_REWARD":
        response["HX-Redirect"] = f"/books/browse"
    elif reward_type == "DAILY_20_FORUMS_POST":
        response["HX-Redirect"] = f"/forums/newsfeed"
    elif reward_type == "FINISH_READING_A_BOOK":
        return HttpResponse("")
    return response


def show_success_posting_in_forums_today_service(request):
    user = request.user
    today = timezone.now().date()

    topic = Topic.objects.filter(author=user, created_at__date=today)
    rewards = ClaimedRewards.objects.filter(
        user=user,
        reward_type="DAILY_20_FORUMS_POST",
        created_at__date=today,
    )

    context = {
        "title": "Great job! You've made 20 forum posts today!",
        "description": "Claim your reward and earn 10 coins!",
        "reward_type": "DAILY_20_FORUMS_POST",
    }

    if topic.count() >= 20 and not rewards:
        return render(request, "components/claim_rewards_modal.html", context)
    else:
        return HttpResponse("")


def pay_using_rewards_coins_service(request, chapter_id):
    user = request.user
    print(chapter_id)
    chapter = get_object_or_404(BooksChapter, id=chapter_id)

    rewards = Rewards.objects.filter(user=user).first()

    if rewards.coins >= 50:
        ChapterUnlockedByUser.objects.create(
            paid_by=user, chapter_id=chapter_id, method_of_payment="via_rewards"
        )
        rewards.coins = rewards.coins - 50
        rewards.save()
        response = JsonResponse({"message": "Unlocking your chapter"})
        response["HX-Redirect"] = f"/book/content/detail/{chapter.slug}"
        return response
    else:
        return render(
            request,
            "components/error_message_alert.html",
            {
                "message": "Insufficient reward coins. You need 50 coins to unlock this chapter."
            },
        )
