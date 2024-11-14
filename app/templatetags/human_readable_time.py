from django import template
import datetime

register = template.Library()


@register.filter
def human_readable_time(minutes):
    try:
        minutes = int(minutes)
    except (ValueError, TypeError):
        return minutes

    if minutes < 60:
        min = "minute" if minutes <= 1 else "minutes"
        return f"{minutes} {min}"
    elif minutes == 60:
        return "1 hour"
    else:
        hours = minutes // 60
        remainder_minutes = minutes % 60
        if remainder_minutes == 0:
            return f"{hours} hours"
        else:
            return f"{hours} hours and {remainder_minutes} minutes"
