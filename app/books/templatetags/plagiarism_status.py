from django import template

from app.enums import plagiarism_checker_state

register = template.Library()


@register.filter
def plagiarism_status(status):
    return plagiarism_checker_state.get(status, "UNKNOWN")
