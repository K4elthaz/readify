from django import template

from app.books.models import UsersFavorites

register = template.Library()


@register.filter
def is_users_favorite(user_id, book_id):
    return UsersFavorites.objects.filter(reader_id=user_id, book_id=book_id).exists()
