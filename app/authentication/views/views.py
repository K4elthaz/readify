import datetime

from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, ListView, DetailView
from google.auth.transport import requests
from google.oauth2 import id_token

from app.authentication.forms import UserProfileForm
from app.authentication.models import User, FollowedAuthor
from app.rewards.models import Rewards
from app.social_newsfeed.models import SocialPost
from app.utils import encrypt_str, generate_random_password
from app.books.models import Categories, Books
from blendjoy.settings import env


# Create your views here.
class SignInView(TemplateView):
    template_name = "signin.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect("/home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the existing context
        context = super().get_context_data(**kwargs)
        environment = env("ENVIRONMENT")
        context["is_locked"] = True if environment == "locked" else False
        return context


class SignUpView(TemplateView):
    template_name = "signup.html"


class SelectRoleView(TemplateView):
    template_name = "select_role.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the existing context
        context = super().get_context_data(**kwargs)
        # Add the URL parameter to the context
        context["id"] = self.kwargs["id"]
        return context


class SelectPreferencesView(TemplateView):
    template_name = "select_preferences.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the existing context
        context = super().get_context_data(**kwargs)
        categories = Categories.objects.all()
        # Add the URL parameter to the context
        context["id"] = self.kwargs["id"]
        context["categories"] = categories
        return context


class FollowAuthorsView(ListView):
    template_name = "follow_authors.html"
    model = User
    context_object_name = "user"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the existing context
        context = super().get_context_data(**kwargs)
        authors = User.objects.filter(user_role="writer").exclude(id=self.kwargs["id"])[
            :5
        ]
        authors_list = [
            {
                "id": author.id,
                "full_name": author.full_name(),
                "username": author.username,
                "profile_picture": author.profile_picture,
                "is_already_followed": FollowedAuthor.objects.filter(
                    user_id=self.kwargs["id"], author_id=author.id
                ).exists(),
            }
            for author in authors
        ]
        context["authors_list"] = authors_list
        # Add the URL parameter to the context
        context["id"] = self.kwargs["id"]
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset


class DoneOnboardingView(TemplateView):
    template_name = "done_onboarding.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the existing context
        context = super().get_context_data(**kwargs)
        # Add the URL parameter to the context
        context["id"] = self.kwargs["id"]
        return context


class UserProfileView(LoginRequiredMixin, DetailView):
    template_name = "user_profile.html"
    login_url = "/signin"
    model = User
    context_object_name = "user_profile"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        id = self.kwargs["pk"]
        user_model = get_object_or_404(User, id=user.id)
        form = UserProfileForm(instance=user_model)
        followed_authors = FollowedAuthor.objects.filter(user=user)
        social_posts = SocialPost.objects.filter(author=user).order_by("-created_at")
        followers = FollowedAuthor.objects.filter(author_id=id)
        published_books = Books.objects.filter(
            author_id=id, is_published=True
        ).order_by("-created_at")
        context["id"] = id
        context["followed_authors"] = followed_authors
        context["num_followed_authors"] = followed_authors.count()
        context["social_posts"] = social_posts
        context["form"] = form
        context["followers"] = followers
        context["num_followers"] = followers.count()
        context["published_books"] = published_books
        context["i_followed"] = FollowedAuthor.objects.filter(
            user=user, author_id=id
        ).exists()
        return context


class ReferralCodeView(TemplateView):
    template_name = "referral_code.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["id"] = self.kwargs["pk"]
        return context


def verify_email(request, email_bytes):
    email = encrypt_str(email_bytes)

    User.objects.filter(email=email).update(is_verified=True)

    return redirect("/signin")


@csrf_exempt
def auth_receiver(request):
    """
    Google calls this URL after the user has signed in with their Google account.
    """
    token = request.POST.get("credential")

    if not token:
        return HttpResponse("No token provided", status=400)

    try:
        user_data = id_token.verify_oauth2_token(
            token, requests.Request(), env("GOOGLE_OAUTH_CLIENT_ID")
        )

        email = user_data["email"]
        user, created = User.objects.get_or_create(
            username=email,
            email=email,
            defaults={
                "is_verified": user_data["email_verified"],
                "first_name": user_data.get("given_name", ""),
                "last_name": user_data.get("family_name", ""),
                "profile_picture": user_data.get("picture", ""),
            },
        )
        rewards = Rewards.objects.filter(user=user)

        if not rewards:
            Rewards.objects.create(user=user)

        # Log the user in directly
        login(request, user)
        request.session["user_data"] = user_data

        if created:
            return redirect(f"/select/role/{user.id}")
        else:
            return redirect("/home")

    except ValueError:
        return HttpResponse("Invalid token", status=403)


class AgreementView(TemplateView):
    template_name = "agreement.html"

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the existing context
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(User, id=self.kwargs["id"])
        # Add the URL parameter to the context
        context["id"] = self.kwargs["id"]
        context["author"] = user.full_name()
        context["date"] = datetime.date.today()
        return context


class ForgotPasswordView(TemplateView):
    template_name = "forgot_password.html"


class ResetPasswordView(TemplateView):
    template_name = "password_reset.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["encrypted_email"] = self.kwargs["encrypted_email"]
        return context


class TermsAndConditionView(TemplateView):
    template_name = "terms_and_conditions.html"
