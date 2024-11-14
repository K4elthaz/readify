from django import template

from app.books.models import ChapterUnlockedByUser

register = template.Library()


@register.filter
def is_unlocked(user_id, chapter_id):
    chapter_unlocked = ChapterUnlockedByUser.objects.filter(
        paid_by_id=user_id, chapter_id=chapter_id
    )

    return chapter_unlocked.exists()
