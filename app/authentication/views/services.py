from typing import List, Any, Union

from asgiref.sync import sync_to_async
from cloudinary import CloudinaryImage
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, get_object_or_404, render

from app.authentication.models import User, FollowedAuthor
from app.notifications.views.services import save_notifications
from app.rewards.models import Rewards
from app.utils import (
    UploadFilesToCloudinary,
    send_email_verification,
    calculate_age_from_string,
    send_password_reset_verification,
    encrypt_str,
)
from app.books.models import Categories


def signup_service(request, *args, **kwargs):
    try:
        profile_picture = request.FILES.get("profile_picture", "")
        username = request.POST.get("username", "")
        first_name = request.POST.get("first_name", "")
        last_name = request.POST.get("last_name", "")
        email = request.POST.get("email", "")
        gender = request.POST.get("gender", "")
        birthday = request.POST.get("birthday", "")
        age = request.POST.get("age", "")
        password = request.POST.get("password", "")

        cloudinary_file_url: str | None = None
        folder: str = "users_profile_pictures"
        file_name: str = (
            f'{folder}/{first_name.lower().replace(" ", "_")}_{last_name.lower().replace(" ", "_")}'
        )

        init_cloudinary: UploadFilesToCloudinary = UploadFilesToCloudinary()
        transformation: List[dict[str, Any]] = [{"width": 100, "height": 100}]

        is_email_exists: bool = User.objects.filter(email=email).exists()

        if is_email_exists:
            raise ValidationError("Email address already exists")

        user: User = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            age=calculate_age_from_string(birthday),
            birthday=birthday,
            gender=gender,
            profile_picture=cloudinary_file_url,
        )

        user.set_password(password)
        user.save()

        if profile_picture:
            init_cloudinary.upload_file(
                profile_picture,
                public_id=file_name,
                transformation=transformation,
            )
            cloudinary_file_url = CloudinaryImage(file_name).build_url()

        user.profile_picture = cloudinary_file_url
        user.save()

        Rewards.objects.create(user=user)
        send_email_verification(email=email)
        response = HttpResponse(
            f"""
            <div class="rounded-md bg-green-50 p-4">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                            <path fill-rule="evenodd"
                                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                                  clip-rule="evenodd"/>
                        </svg>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm font-medium text-green-800">You've successfully created your account. Redirecting...</p>
                    </div>
                    <div class="ml-auto pl-3">
                        <div class="-mx-1.5 -my-1.5">
                        </div>
                    </div>
                </div>
            </div>
        """
        )
        response["HX-Redirect"] = f"/select/role/{user.id}"
        return response
    except Exception as e:

        return render(
            request,
            "components/error_message_alert.html",
            {"message": str(e)},
        )


def select_role_service(request, id, role):
    user = User.objects.filter(id=id).update(user_role=role)
    response = JsonResponse({"message": "Account type selected"})

    if role == "reader":
        response["HX-Redirect"] = f"/select/preferences/{id}"
    else:
        response["HX-Redirect"] = f"/agreement/{id}"
    return response


def select_preferences_service(request, id):
    preferences = request.POST.get("preferences", "")
    onboarding_info = [{"book_preferences": preferences.split(", ")}]
    user = User.objects.filter(id=id).update(onboarding=onboarding_info)
    response = JsonResponse({"message": "User preferences selected"})
    response["HX-Redirect"] = f"/authors/follow/{id}"
    return response


def follow_author_service(request, id, author_id):
    select_author = FollowedAuthor.objects.create(
        user_id=id,
        author_id=author_id,
    )
    author = User.objects.filter(id=author_id).first()

    notification_message = f"""<p class="text-sm font-semibold text-gray-900">You have a new follower!</p>
        <hr>
        <p class="mt-2 text-xs text-gray-500">
            <span class="font-semibold text-gray-900">{select_author.user.full_name()}</span> followed you!
        </p>
    """
    save_notifications(user=author, message=notification_message)
    response = JsonResponse({"message": "Author followed"})
    response["HX-Redirect"] = f"/authors/follow/{id}"
    return response


def signin_service(request):
    try:
        username: str = request.POST.get("username", "")
        password: str = request.POST.get("password", "")

        is_user_exists: bool = User.objects.filter(username=username).exists()

        if not is_user_exists:
            raise Exception("User account does not exists.")

        user_auth: Union[User, None] = authenticate(
            username=username, password=password
        )

        if user_auth:
            user = get_object_or_404(User, username=username)
            login(request, user)
            response = JsonResponse({"message": "Author followed"})
            response["HX-Redirect"] = f"/home"
            return response
        else:
            raise Exception(f"Invalid username or password. Please try again.")
    except Exception as ex:
        return render(
            request,
            "components/error_message_alert.html",
            {"message": str(ex)},
        )


def logout_service(request):
    logout(request)
    response = JsonResponse({"message": "Sign out successful."})
    response["HX-Redirect"] = f"/signin"
    return response


def unfollow_service(request, id):
    user = request.user
    author = FollowedAuthor.objects.filter(user=user, author_id=id).exists()
    if author:
        FollowedAuthor.objects.filter(user=user, author_id=id).delete()
        response = JsonResponse({"message": "Sign out successful."})
        response["HX-Redirect"] = f"/profile/{id}"
        return response
    else:
        FollowedAuthor.objects.filter(user=user, id=id).delete()
        response = JsonResponse({"message": "Sign out successful."})
        response["HX-Redirect"] = f"/profile/{user.id}"
        return response


def referral_code_service(request, id):
    username = request.POST.get("username", "")
    user = User.objects.filter(username=username).first()

    if user:
        reward = Rewards.objects.filter(user=user).first()
        reward.coins = reward.coins + 20
        reward.save()
        response = JsonResponse({"message": "Sign out successful."})
        response["HX-Redirect"] = f"/onboarding/done/{id}"
        return response
    else:
        return render(
            request,
            "components/error_message_alert.html",
            {
                "message": "Username not found. The user either does not exist, or you can skip this step."
            },
        )


def update_user_profile(request):

    user = request.user

    first_name = request.POST.get("first_name", "")
    last_name = request.POST.get("last_name", "")
    email = request.POST.get("email", "")
    username = request.POST.get("username", "")
    gender = request.POST.get("gender", "")
    birthday = request.POST.get("birthday", "")

    User.objects.filter(id=user.id).update(
        first_name=first_name,
        last_name=last_name,
        email=email,
        username=username,
        gender=gender,
        birthday=birthday,
        age=calculate_age_from_string(birthday),
    )

    response = HttpResponse(
        f"""
                <div class="rounded-md bg-green-50 p-4">
                    <div class="flex">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                <path fill-rule="evenodd"
                                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                                      clip-rule="evenodd"/>
                            </svg>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm font-medium text-green-800">You've successfully updated your profile. Redirecting...</p>
                        </div>
                        <div class="ml-auto pl-3">
                            <div class="-mx-1.5 -my-1.5">
                            </div>
                        </div>
                    </div>
                </div>
            """
    )
    response["HX-Redirect"] = f"/profile/{user.id}"
    return response


def change_password(request):
    current_password = request.POST.get("current_password", "")
    new_password = request.POST.get("new_password", "")
    confirm_password = request.POST.get("confirm_password", "")

    user = request.user  # The logged-in user
    user_session = request.session.get("user_data", False)

    if not user_session or user.password:
        # Check if the current password is correct
        if not check_password(current_password, user.password):
            return render(
                request,
                "components/error_message_alert.html",
                {"message": "Invalid Current Password. Please try again to continue"},
            )

    # Check if the new password matches the confirm password
    if new_password != confirm_password:
        return render(
            request,
            "components/error_message_alert.html",
            {
                "message": "New password and Confirm Password do not match. Please try again to continue."
            },
        )

    # If everything is correct, update the password
    user.set_password(new_password)
    user.save()

    # Keep the user logged in after password change
    update_session_auth_hash(request, user)

    response = JsonResponse({"message": "Password change successful."})
    response["HX-Redirect"] = f"/profile/{user.id}"
    return response


@sync_to_async
def forgot_password_service(request):

    email = request.POST.get("email", "")

    user = User.objects.filter(email=email)

    if user.exists():
        send_password_reset_verification(email=email)
        return render(request, "components/success_email_sent.html")
    else:
        return render(
            request,
            "components/error_message_alert.html",
            {
                "message": "Email address not found or invalid. Please try again to continue."
            },
        )


@sync_to_async
def reset_password_service(request, encrypted_email):

    new_password = request.POST.get("new_password", "")
    confirm_password = request.POST.get("confirm_password", "")

    if new_password != confirm_password:
        return render(
            request,
            "components/error_message_alert.html",
            {
                "message": "New password and confirmation do not match. Please try again."
            },
        )
    else:
        email = encrypt_str(encrypted_email)
        user = User.objects.filter(email=email).first()
        user.set_password(new_password)
        user.save()
        response = JsonResponse({"message": "Password change successful."})
        response["HX-Redirect"] = f"/signin"
        return response
