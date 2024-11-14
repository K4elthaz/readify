from django.contrib import admin
from unfold.admin import ModelAdmin

from app.books.forms import BookContentForm
from app.books.models import (
    Books,
    BooksChapter,
    Categories,
    ChapterUnlockedByUser,
    PlagiarismCheckerLogs,
)


# Register your models here.


@admin.register(Books)
class BooksAdmin(ModelAdmin):
    change_form_template = "custom_admin_actions/view_books_site.html"


@admin.register(BooksChapter)
class BooksChapterAdmin(ModelAdmin):
    form = BookContentForm


@admin.register(Categories)
class CategoryAdmin(ModelAdmin):
    pass


@admin.register(ChapterUnlockedByUser)
class ChapterUnlockedByUserAdmin(ModelAdmin):
    pass


@admin.register(PlagiarismCheckerLogs)
class PlagiarismCheckerLogsAdmin(ModelAdmin):
    list_display = ("book", "chapter", "log_id", "words_count", "percent_value")

    # Add percent_value to readonly fields, not fieldsets
    readonly_fields = ("percent_value",)

    # Custom field to display the "percent" from the results JSON
    @admin.display(description="Plagiarism Percent")
    def percent_value(self, obj):
        try:
            return f"{obj.results['data']['report']['percent']} %"
        except (KeyError, TypeError):
            return "N/A"  # Fallback if the key is not found

    # Optional: Customize the admin detail view with other fields
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "book",
                    "chapter",
                    "log_id",
                    "words_count",
                )  # Exclude percent_value here
            },
        ),
        (
            "Plagiarism Details",
            {
                "fields": ("percent_value",),  # Place readonly field here
            },
        ),
    )
