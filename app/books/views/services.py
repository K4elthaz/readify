from typing import List, Any
from urllib.parse import urlparse

from asgiref.sync import sync_to_async
from cloudinary import CloudinaryImage
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, render
from django.utils.html import format_html

from app.authentication.models import FollowedAuthor, User
from app.books.forms import BookContentForm
from app.enums import StartReadingChapter
from app.notifications.models import Notifications
from app.notifications.views.services import save_notifications
from app.tasks import run_plagiarism_checker_tasks, run_plagiarism_report_tasks
from app.utils import UploadFilesToCloudinary
from app.books.models import (
    Books,
    Categories,
    BooksChapter,
    UsersStartedChapter,
    UsersFavorites,
    ChapterUnlockedByUser,
    Rates,
    InviteCollaborators,
)


def save_new_book_service(request):
    try:
        title = request.POST.get("title", "")
        description = request.POST.get("description", "")
        cover_photo = request.FILES.get("cover_photo", "")
        category = request.POST.getlist("category")
        is_published = request.POST.get("is_published", False)

        cloudinary_file_url: str | None = None
        folder: str = "books_cover_photo"
        file_name: str = f'{folder}/{title.lower().replace(" ", "_")}'

        init_cloudinary: UploadFilesToCloudinary = UploadFilesToCloudinary()
        transformation: List[dict[str, Any]] = [{"width": 200, "height": 200}]

        create_book_query: Books = Books.objects.create(
            title=title,
            description=description,
            author=request.user,
            cover_photo=cloudinary_file_url,
            is_published=is_published,
        )

        if cover_photo:
            init_cloudinary.upload_file(
                cover_photo, public_id=file_name, transformation=transformation
            )
            cloudinary_file_url = CloudinaryImage(file_name).build_url()

        create_book_query.cover_photo = cloudinary_file_url
        create_book_query.save()

        # Add categories to the book
        categories = Categories.objects.filter(id__in=category)
        create_book_query.category.add(*categories)

        response = JsonResponse({"message": "Book created successfully"})
        response["HX-Redirect"] = f"/book/detail/{create_book_query.slug}"
        return response
    except Exception as e:
        raise e


def save_new_content_service(request, slug):

    title = request.POST.get("title", "")
    is_draft = request.POST.get("is_draft", False)
    is_locked = request.POST.get("is_locked", False)
    content = request.POST.get("content", "")

    book: Books = Books.objects.filter(slug=slug).first()
    # Check if the chapter number already exists for the given book
    # is_chapter_number_exists: bool = BooksChapter.objects.filter(
    #     Q(chapter_number=chapter_number) & Q(book_id=book.id)
    # ).exists()
    #
    # if is_chapter_number_exists:
    #     return render(
    #         request,
    #         "components/error_message_alert.html",
    #         {"message": "Chapter number already exists for this book"},
    #     )

    try:
        # Attempt to get the latest chapter
        current_chapter = (
            BooksChapter.objects.only("chapter_number")
            .filter(book=book, is_archived=False)
            .latest("created_at")
        )
        new_chapter_number = current_chapter.chapter_number + 1
    except ObjectDoesNotExist:
        # If no chapter exists, set the current chapter number to 1
        new_chapter_number = 1

    # Create a new chapter
    new_chapter = BooksChapter.objects.create(
        title=title,
        chapter_number=new_chapter_number,
        book_id=book.id,
        content=content,
        is_draft=is_draft,
        is_locked=is_locked,
    )

    run_plagiarism_checker_tasks.delay(slug=new_chapter.slug)

    response = JsonResponse({"message": "Book content created successfully"})
    response["HX-Redirect"] = f"/book/detail/{slug}"
    return response


def check_if_book_already_started(request: HttpRequest, chapter_slug: str):
    # Retrieve the current chapter
    chapter = BooksChapter.objects.filter(slug=chapter_slug).first()
    if not chapter:
        return render(
            request,
            "components/error_message_alert.html",
            {"message": "Chapter number already exists for this book"},
        )

    # Update the status of the current chapter to 'DONE'
    UsersStartedChapter.objects.filter(reader=request.user, chapter=chapter).update(
        status=StartReadingChapter.DONE.value
    )

    # Find the next chapter based on the created date
    next_chapter = (
        BooksChapter.objects.filter(
            book=chapter.book, is_draft=False, created_at__gt=chapter.created_at
        )
        .order_by("created_at")
        .first()
    )

    if not next_chapter:
        return {
            "status_code": 200,
            "message": "You have completed all chapters in this book.",
        }

    return {
        "status_code": 200,
        "message": "Chapter marked as done.",
        "next_chapter_slug": next_chapter.slug,
        "next_chapter_title": next_chapter.title,
    }


def next_chapter_service(request, slug):
    user = request.user
    # Get the current chapter by slug
    chapter = get_object_or_404(BooksChapter, slug=slug)

    next_item = (
        BooksChapter.objects.filter(
            book=chapter.book,  # Ensure it's from the same book
            created_at__gt=chapter.created_at,  # Get chapters created after the current one
        )
        .order_by("created_at")  # Order by creation time to get the next one
        .first()
    )

    is_next_chapter_unlocked = ChapterUnlockedByUser.objects.filter(
        paid_by=user, chapter=next_item
    )

    if next_item:
        if not next_item.is_locked:
            response = JsonResponse({"message": "Going to next chapter"})
            response["HX-Redirect"] = f"/book/content/detail/{next_item.slug}"
            return response
        else:
            if is_next_chapter_unlocked:
                response = JsonResponse({"message": "Going to next chapter"})
                response["HX-Redirect"] = f"/book/content/detail/{next_item.slug}"
                return response
            return render(
                request,
                "components/error_message_alert.html",
                {
                    "message": "Sorry. Next chapter is currently locked. Unlocked it first to continue reading"
                },
            )
    else:
        # If there are no more chapters, render a modal or response indicating completion
        return render(
            request,
            "components/done_reading_all_chapters_modal.html",
            {"url": f"/book/detail/{chapter.book.slug}"},
        )


def previous_chapter_service(request, slug):
    # Get the current chapter by slug
    chapter = get_object_or_404(BooksChapter, slug=slug)
    user = request.user
    prev_item = (
        BooksChapter.objects.filter(
            book=chapter.book,  # Ensure it's from the same book
            created_at__lt=chapter.created_at,  # Get chapters created after the current one
        )
        .order_by("created_at")  # Order by creation time to get the next one
        .first()
    )
    is_prev_chapter_unlocked = ChapterUnlockedByUser.objects.filter(
        paid_by=user, chapter=prev_item
    )
    if prev_item:
        if not prev_item.is_locked:
            response = JsonResponse({"message": "Going to previous chapter"})
            response["HX-Redirect"] = f"/book/content/detail/{prev_item.slug}"
            return response
        else:
            if is_prev_chapter_unlocked:
                response = JsonResponse({"message": "Going to previous chapter"})
                response["HX-Redirect"] = f"/book/content/detail/{prev_item.slug}"
                return response
            return render(
                request,
                "components/error_message_alert.html",
                {
                    "message": "Sorry. Previous chapter is currently locked. Unlocked it first to continue reading"
                },
            )
    else:
        # If there are no more chapters, render a modal or response indicating completion
        return render(
            request,
            "components/done_reading_all_chapters_modal.html",
            {"url": f"/book/detail/{chapter.book.slug}"},
        )


def remove_chapter_service(request, book_slug, chapter_slug):
    book_chapter = BooksChapter.objects.filter(slug=chapter_slug).update(
        is_archived=True
    )
    response = HttpResponse(
        f"""
            <div class="rounded-md bg-green-50 p-4">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor"
                             aria-hidden="true">
                            <path fill-rule="evenodd"
                                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                                  clip-rule="evenodd"/>
                        </svg>
                    </div>
                    <div class="ml-3">
                        <p class="text-sm font-medium text-green-800">You have successfully deleted this chapter</p>
                    </div>
                    <div class="ml-auto pl-3">
                        <div class="-mx-1.5 -my-1.5">
                        </div>
                    </div>
                </div>
            </div>
        """
    )
    response["HX-Redirect"] = f"/book/detail/{book_slug}"
    return response


@sync_to_async
def delete_book_service(request, slug):
    Books.objects.filter(slug=slug).delete()
    response = JsonResponse({"message": "Books successfully deleted"})
    response["HX-Redirect"] = f"/books/library"
    return response


@sync_to_async
def publish_book_service(request, slug):
    user = request.user
    Books.objects.filter(slug=slug).update(is_published=True)
    notification_message = f"""
       <p class="text-sm font-semibold text-gray-900">New book alert!</p>
       <hr>
       <p class="mt-2 text-xs text-gray-500">
           <span class="font-semibold text-gray-900">{user.full_name()}</span>
           published a new book. View it <a href="/book/detail/{slug}" class="text-pink-500 underline">here</a>.
       </p>
    """

    # Get all followers of the author
    followers = FollowedAuthor.objects.filter(author=user)
    if followers.exists():
        print(f"Followers: {followers.count()} found")

        # Notify each follower
        for follower in followers:
            print(f"Notifying: {follower.user.full_name()}")
            save_notifications(user=follower.user, message=notification_message)
    else:
        print("No followers found for the author")
    response = JsonResponse({"message": "Books successfully published"})
    response["HX-Redirect"] = f"/book/detail/{slug}"
    return response


@sync_to_async
def unpublish_book_service(request, slug):
    user = request.user
    Books.objects.filter(slug=slug).update(is_published=False)
    response = JsonResponse({"message": "Books successfully unpublished"})
    response["HX-Redirect"] = f"/book/detail/{slug}"
    return response


@sync_to_async
def add_to_favorites(request, slug):
    user = request.user
    book = Books.objects.filter(slug=slug).first()
    UsersFavorites.objects.update_or_create(book=book, reader=user)
    response = JsonResponse({"message": "Books successfully added to favorites"})
    response["HX-Redirect"] = f"/book/detail/{slug}"
    return response


@sync_to_async
def follow_author_service(request, author_id):
    user = request.user
    referer_url = request.META.get("HTTP_REFERER", "/")

    # Parse the URL
    parsed_url = urlparse(referer_url)

    # Get the path and split it to find the last segment
    path_segments = parsed_url.path.strip("/").split("/")

    # Get the last segment (or '/' if it's the root)
    last_segment = path_segments[-1] if path_segments else "/"
    FollowedAuthor.objects.create(
        user=user,
        author_id=author_id,
    )
    if author_id == last_segment:
        response = JsonResponse({"message": "Author followed"})
        response["HX-Redirect"] = f"/profile/{last_segment}"
        return response
    else:
        response = JsonResponse({"message": "Author followed"})
        response["HX-Redirect"] = f"/books/browse"
        return response


@sync_to_async
def search_service(request):
    user = request.user
    query = request.GET.get("search", False)

    if query:
        books_queryset = Books.objects.filter(
            Q(title__icontains=query) & Q(is_published=True)
        )

        authors_queryset = User.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(username__icontains=query)
            | Q(email__icontains=query),
            user_role="writer",
        )

        if books_queryset:
            return render(
                request,
                "search/search_books.html",
                {"books": books_queryset},
            )

        elif authors_queryset:
            authors = [
                {
                    "id": author.id,
                    "full_name": author.full_name(),
                    "username": author.username,
                    "profile_picture": author.profile_picture,
                    "num_of_authored_books": Books.objects.filter(
                        author_id=author.id
                    ).count(),
                    "is_already_followed": FollowedAuthor.objects.filter(
                        user=user, author_id=author.id
                    ).exists(),
                }
                for author in authors_queryset
            ]
            return render(
                request,
                "search/search_author.html",
                {"authors": authors},
            )

        else:
            return HttpResponse(
                """
                <main class="grid min-h-full place-items-center bg-white px-6 py-24 sm:py-32 lg:px-8">
                  <div class="text-center">
                    <p class="text-base font-semibold text-pink-600">404</p>
                    <h1 class="mt-4 text-3xl font-bold tracking-tight text-gray-900 sm:text-5xl">Search result not found</h1>
                    <p class="mt-6 text-base leading-7 text-gray-600">Sorry, we couldn’t find what you’re looking for.</p>
                    <div class="mt-10 flex items-center justify-center gap-x-6">
                    </div>
                  </div>
                </main>
            """
            )
    else:
        response = JsonResponse({"message": "Search empty"})
        response["HX-Redirect"] = f"/books/browse"
        return response


@sync_to_async
def update_book_content_service(request, slug):
    title = request.POST.get("title", "")
    is_draft = request.POST.get("is_draft", False)
    is_locked = request.POST.get("is_locked", False)
    content = request.POST.get("content", "")

    # Create a new chapter
    BooksChapter.objects.filter(slug=slug).update(
        title=title,
        content=content,
        is_draft=is_draft,
        is_locked=is_locked,
    )

    run_plagiarism_checker_tasks.delay(slug=slug)
    response = JsonResponse({"message": "Book content updated successfully"})
    response["HX-Redirect"] = f"/book/content/detail/{slug}"
    return response


@sync_to_async
def search_collab_service(request, slug):
    search = request.GET.get("search", "")
    user = request.user
    if search:
        # Get co-authors' IDs for books authored by the given user, excluding None values
        co_authors_ids = (
            Books.objects.filter(author=user, slug=slug)
            .exclude(co_authors__isnull=True)
            .values_list("co_authors__id", flat=True)
            .distinct()
        )  # Extract the co_authors' IDs without duplicates

        # Search for authors based on the search term and exclude co-authors and the current user
        authors = (
            User.objects.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(username__icontains=search)
                | Q(email__icontains=search),
                user_role="writer",
            )
            .exclude(id__in=co_authors_ids)  # Exclude existing co-authors
            .exclude(id=user.id)  # Exclude the current user
        )
        return render(
            request,
            "search/search_collab.html",
            {"authors": authors},
        )
    else:
        return render(
            request,
            "search/search_collab.html",
            {"authors": []},
        )


@sync_to_async
def invite_collaborator(request, slug):
    preferences = request.POST.get("preferences", "")
    user = request.user
    if preferences:
        books = Books.objects.filter(slug=slug).first()
        co_authors_count = books.co_authors.count()
        invited_collaborator = InviteCollaborators.objects.filter(
            invited_by=user, status="pending"
        )

        if invited_collaborator:
            if invited_collaborator.count() >= 5:
                return render(
                    request,
                    "components/error_message_alert.html",
                    {"message": "Oops! You can invite a maximum of 5 co-authors only."},
                )

        if co_authors_count >= 5:
            return render(
                request,
                "components/error_message_alert.html",
                {"message": "Oops! You can add a maximum of 5 co-authors only."},
            )

        if books:
            invited_co_authors = preferences.split(", ")
            for invited in invited_co_authors:
                InviteCollaborators.objects.create(
                    invited_by=user, co_author_id=invited
                )
                invited_user = User.objects.get(id=invited)
                notif = Notifications.objects.create(user=invited_user)
                print(notif.id)
                # Update the notification message after creating the object
                notification_message = f"""
                   <p class="text-sm font-semibold text-gray-900">New Invitations!</p>
                   <hr>
                   <p class="mt-2 text-xs text-gray-500">
                       <span class="font-semibold text-gray-900">{user.full_name()}</span>
                       invited you to co-author <span class="font-semibold text-gray-900">"{books.title}"</span><br>
                       <div class="flex gap-x-2">
                           <a hx-post="/collaborations/respond/{slug}/accepted/{notif.id}/" class="text-blue-500 text-xs hover:underline cursor-pointer">Accept Invite</a>
                           <a hx-post="/collaborations/respond/{slug}/decline/{notif.id}/" class="text-red-500 text-xs hover:underline cursor-pointer">Decline Invite</a>
                       </div>
                   </p>
                """

                # Update the notification with the formatted message
                Notifications.objects.filter(id=notif.id).update(
                    message=notification_message
                )
            # books.co_authors.add(*preferences.split(", "))
            response = JsonResponse({"message": "Search empty"})
            response["HX-Redirect"] = f"/book/detail/{slug}"
            return response
        books.co_authors.set(preferences.split(", "))
        response = JsonResponse({"message": "Search empty"})
        response["HX-Redirect"] = f"/book/detail/{slug}"
        return response


@sync_to_async
def refresh_plagiarism_reports(request, slug):
    run_plagiarism_report_tasks.delay(slug=slug)
    return render(
        request,
        "components/success_message_alert.html",
    )


@sync_to_async
def write_a_review(request, slug):
    user = request.user
    rate = request.POST.get("rate", "")
    review = request.POST.get("review", "")

    book = get_object_or_404(Books, slug=slug)
    Rates.objects.create(book=book, count=rate, review=review, user=user)
    notification_message = f"""
        <p class="text-sm font-semibold text-gray-900">New review for your book!</p>
        <hr>
        <p class="mt-2 text-xs text-gray-500">
            {user.full_name()} sent a review to your book. See it <a href="/book/detail/{slug}" class="text-pink-500 underline">here</a>.
        </p>
    """
    save_notifications(user=book.author, message=notification_message)
    response = JsonResponse({"message": "Review succesfully posted"})
    response["HX-Redirect"] = f"/book/detail/{slug}"
    return response


@sync_to_async
def respond_to_invitations(request, book_slug, status, id):
    user = request.user

    response = JsonResponse({"message": "Responded to invitations"})
    if status == "accepted":
        books = Books.objects.filter(slug=book_slug).first()
        books.co_authors.add(user.id)
        response["HX-Redirect"] = f"/book/detail/{book_slug}"
    else:
        response["HX-Redirect"] = f"/dashboard"

    invited = InviteCollaborators.objects.filter(co_author_id=user.id).first()
    print(invited)
    invited.status = status
    invited.save()

    books = Books.objects.filter(author=invited.invited_by).first()
    accepted_invite_message = (
        '<p class="text-blue-500 text-xs underline">Invite Accepted</p>'
    )
    declined_invite_message = (
        '<p class="text-red-500 text-xs underline">Invite Declined</p>'
    )

    updated_message = (
        accepted_invite_message if status == "accepted" else declined_invite_message
    )
    notification_message = f"""
       <p class="text-sm font-semibold text-gray-900">New Invitations!</p>
       <hr>
       <p class="mt-2 text-xs text-gray-500">
           <span class="font-semibold text-gray-900">{invited.invited_by.full_name()}</span>
           invited you to co-author <span class="font-semibold text-gray-900">"{books.title}"</span><br>
           <div class="flex gap-x-2">
           {updated_message}
           </div>
       </p>
    """
    Notifications.objects.filter(id=id).update(message=notification_message)

    return response


def update_book_service(request, slug):
    try:
        # Extract data from the request
        title = request.POST.get("title", "")
        description = request.POST.get("description", "")
        cover_photo = request.FILES.get("cover_photo", "")
        category_ids = request.POST.getlist("category")
        is_published = bool(request.POST.get("is_published", False))

        # Prepare Cloudinary variables
        cloudinary_file_url: str | None = None
        folder: str = "books_cover_photo"
        file_name: str = f'{folder}/{title.lower().replace(" ", "_")}'

        # Initialize Cloudinary uploader
        cloudinary_uploader = UploadFilesToCloudinary()
        transformation: List[dict[str, Any]] = [{"width": 200, "height": 200}]

        # Get the book instance by slug and update its details
        book_instance: Books = Books.objects.get(slug=slug)
        book_instance.title = title
        book_instance.description = description
        book_instance.author = request.user
        book_instance.is_published = is_published

        # If a new cover photo is uploaded, update the Cloudinary image
        if cover_photo:
            cloudinary_uploader.upload_file(
                cover_photo, public_id=file_name, transformation=transformation
            )
            cloudinary_file_url = CloudinaryImage(file_name).build_url()
            book_instance.cover_photo = cloudinary_file_url

        # Save updated book instance
        book_instance.save()

        # Update the book's categories
        categories = Categories.objects.filter(id__in=category_ids)
        book_instance.category.set(categories)  # Use 'set' to replace categories

        # Respond with a success message and redirect
        response = JsonResponse({"message": "Book updated successfully"})
        response["HX-Redirect"] = f"/book/detail/{book_instance.slug}"
        return response

    except Books.DoesNotExist:
        return JsonResponse({"error": "Book not found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
