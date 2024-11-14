from django import template

from app.books.models import UsersFavorites

register = template.Library()


@register.filter
def total_reader(id):
    count = UsersFavorites.objects.filter(book_id=id).count()
    label = "reader" if count <= 1 else "readers"
    return f"{count} {label}"
