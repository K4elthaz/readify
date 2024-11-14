from datetime import timedelta

from asgiref.sync import sync_to_async
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg
from django.db.models.functions import TruncDate
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from app.authentication.models import FollowedAuthor
from app.books.models import Books, UsersFavorites, Rates


# Create your views here.


class LandingPageView(TemplateView):
    template_name = "landing_page.html"


class HomepageView(LoginRequiredMixin, TemplateView):
    template_name = "homepage.html"
    login_url = "/signin"


@login_required(login_url="/signin")
def homepage(request):
    if request.user.user_role == "writer":
        return redirect("/dashboard")
    elif request.user.user_role == "tech_support":
        return redirect("/messages")
    else:
        return redirect("/books/browse")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"
    login_url = "/signin"


@sync_to_async
def analytics_service(request):
    user = request.user
    # Get the current time
    now = timezone.now()

    seven_days_ago = now - timedelta(days=7)

    total_books = Books.objects.filter(author=user)
    total_published_books = Books.objects.filter(author=user, is_published=True)
    total_draft_books = Books.objects.filter(author=user, is_published=False)

    total_followers = FollowedAuthor.objects.filter(author=user)
    total_favorited_books_per_day = (
        UsersFavorites.objects.filter(created_at__gte=seven_days_ago, book__author=user)
        .annotate(day=TruncDate("created_at"))  # Truncate to date
        .values("day")  # Group by day
        .annotate(favorites_count=Count("id"))  # Count the number of favorites per day
        .order_by("day")  # Order by the day (optional)
    )
    # Get the total count of ratings per book grouped by the `count` field
    book_rate_counts = (
        Rates.objects.filter(book__author=user)
        .values("book__title", "count")
        .annotate(total_count=Count("count"))
        .order_by("-count")
    )

    context = {
        "total_books": total_books.count(),
        "total_published_books": total_published_books.count(),
        "total_draft_books": total_draft_books.count(),
        "total_followers": total_followers.count(),
        "total_favorited_books_per_day": total_favorited_books_per_day,
        "book_rate_counts": book_rate_counts,
    }

    return render(request, "analytics.html", context)
