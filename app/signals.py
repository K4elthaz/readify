from django.db.models.signals import post_save
from django.dispatch import receiver

from app.authentication.models import FollowedAuthor
from app.books.models import BooksChapter
from app.notifications.views.services import save_notifications


@receiver(post_save, sender=BooksChapter)
def notify_followers_for_new_chapter(sender, instance, created, **kwargs):
    # Ensure that the signal only triggers when a new chapter is created
    if created:

        # Debugging and logging output to check values
        print(f"Is locked: {instance.is_locked}, Is draft: {instance.is_draft}")

        # Ensure the book and author are available and valid
        if hasattr(instance, "book") and hasattr(instance.book, "author"):
            print(f"Author: {instance.book.author.full_name()}")

            # Only notify followers if the chapter is not locked and not a draft
            if (
                instance.is_locked == "False"
                and instance.is_draft == "False"
                and instance.book.is_published == "False"
            ):
                notification_message = f"""
                               <p class="text-sm font-semibold text-gray-900">New chapter!</p>
                               <hr>
                               <p class="mt-2 text-xs text-gray-500">
                                   <span class="font-semibold text-gray-900">{instance.book.author.full_name()}</span>
                                   published a new book chapter. View it <a href="/book/content/detail/{instance.slug}" class="text-pink-500 underline">here</a>.
                               </p>
                           """

                # Get all followers of the author
                followers = FollowedAuthor.objects.filter(author=instance.book.author)
                if followers.exists():
                    print(f"Followers: {followers.count()} found")

                    # Notify each follower
                    for follower in followers:
                        print(f"Notifying: {follower.user.full_name()}")
                        save_notifications(
                            user=follower.user, message=notification_message
                        )
                else:
                    print("No followers found for the author")
        else:
            print("Book or author information is missing")
