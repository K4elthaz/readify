import math

from autoslug import AutoSlugField
from ckeditor.fields import RichTextField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Func, F, Count
from django_tiptap.fields import TipTapTextField

from app.enums import StartReadingChapter
from app.models import BaseModel


class Round(Func):
    function = "ROUND"
    template = "%(function)s(%(expressions)s)"


class Lowercase(Func):
    function = "LOWER"
    template = "%(function)s(%(expressions)s)"


# Create your models here.
class Categories(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lowercase("name"), name="unique_lowercase_name")
        ]

        db_table = "categories"
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Books(BaseModel):
    title = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    author = models.ForeignKey(
        "authentication.User", on_delete=models.CASCADE, related_name="book_author"
    )
    cover_photo = models.CharField(max_length=255, null=True, blank=True)
    category = models.ManyToManyField(Categories, blank=True)
    is_published = models.BooleanField(default=True)
    slug = AutoSlugField(populate_from="title")

    co_authors = models.ManyToManyField(
        "authentication.User", blank=True, related_name="books_co_author"
    )

    class Meta:
        db_table = "books"
        verbose_name = "Book Library"
        verbose_name_plural = "Book Libraries"

    def __str__(self):
        return self.title


class BooksChapter(BaseModel):
    book = models.ForeignKey("Books", on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=255)
    chapter_number = models.IntegerField()
    images = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField()
    is_draft = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    slug = AutoSlugField(populate_from="title")

    class Meta:
        db_table = "books_chapter"
        verbose_name = "Chapter per book"
        verbose_name_plural = "Chapters per book"

    def __str__(self):
        return f"Chapter {self.chapter_number}: {self.title} | Book: {self.book.title}"

    def get_reading_time(self) -> int:
        word_count: int = len(self.content.split())
        reading_speed_wpm: int = 200  # average reading speed in words per minute
        reading_time_minutes: int = math.ceil(word_count / reading_speed_wpm)
        return reading_time_minutes


class UsersStartedChapter(BaseModel):
    STATUS_CHOICES = [(key.value, key.name) for key in StartReadingChapter]

    chapter = models.ForeignKey(
        "BooksChapter", on_delete=models.CASCADE, related_name="started_chapters"
    )
    reader = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="books_chapter_reader",
        verbose_name="Reader",
        help_text="The user associated with this record.",
    )

    status = models.CharField(max_length=100, choices=STATUS_CHOICES)

    class Meta:
        managed = True
        db_table = "users_started_chapter"
        verbose_name = "User's Started Chapter"

    def __str__(self):
        return f"Chapter {self.chapter.chapter_number}: {self.chapter.title}"


class UsersFavorites(BaseModel):
    """A model representing the association between a user and a book in the library,
    including the chapters the user has read.
    """

    book = models.ForeignKey(
        "Books",
        on_delete=models.CASCADE,
        related_name="user_libraries",
        verbose_name="Book",
        help_text="The book associated with this record.",
    )
    reader = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="library_books",
        verbose_name="Reader",
        help_text="The user associated with this record.",
    )

    class Meta:
        managed = True
        db_table = "users_favorites"
        verbose_name = "User's Favorites"
        verbose_name_plural = "User's Favorites"
        unique_together = (("book", "reader"),)
        constraints = [
            models.UniqueConstraint(
                fields=["book", "reader"], name="unique_reader_book"
            )
        ]

    def __str__(self):
        return f"{self.reader.username} - {self.book.title}"


class ChapterUnlockedByUser(BaseModel):
    chapter = models.ForeignKey(
        BooksChapter, on_delete=models.CASCADE, related_name="unlocked_chapter"
    )
    paid_by = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="unlocked_for_user",
    )
    method_of_payment = models.CharField(max_length=255)

    class Meta:
        db_table = "chapter_unlocked_by_user"
        verbose_name = "Chapter Unlocked By User"
        verbose_name_plural = "Chapter Unlocked By User"

    def __str__(self):
        return f"{self.chapter.title} unlocked by {self.paid_by.full_name()} via {self.method_of_payment}"


class PlagiarismCheckerLogs(BaseModel):
    book = models.ForeignKey(
        Books, on_delete=models.CASCADE, related_name="books_checked"
    )
    chapter = models.ForeignKey(
        BooksChapter, on_delete=models.CASCADE, related_name="book_chapter_checked"
    )

    log_id = models.CharField(max_length=10)
    words_count = models.IntegerField()
    results = models.JSONField(default=dict)

    class Meta:
        db_table = "plagiarism_checker_logs"
        verbose_name = "Plagiarism Checker Logs"
        verbose_name_plural = "Plagiarism Checker Logs"

    def __str__(self):
        return f"{self.chapter.title}"


class Rates(BaseModel):
    book = models.ForeignKey(
        "Books", on_delete=models.CASCADE, related_name="rates_per_book"
    )
    count = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.CharField(max_length=500)
    user = models.ForeignKey(
        "authentication.User", on_delete=models.CASCADE, related_name="books_rated_by"
    )

    class Meta:
        db_table = "rates"
        verbose_name = "Rate"
        verbose_name_plural = "Rates"

    def total_rates(self):
        # Assuming you want to calculate the total rates for a specific book
        return Rates.objects.filter(book=self.book).count()

    def get_total_rates_per_book(self):
        total_counts = Rates.objects.filter(book=self.book).count()

        return (
            Rates.objects.filter(book=self.book)
            .values("count")
            .annotate(
                total=Count("count"),
                percentage=Round(F("total") * 100.0 / total_counts),
            )
            .order_by("-count")
        )


class Comments(BaseModel):
    book = models.ForeignKey("Books", on_delete=models.CASCADE)
    comment_by = models.ForeignKey("authentication.User", on_delete=models.CASCADE)
    comment = models.TextField()

    class Meta:
        db_table = "comments"
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return f"Comment: {self.comment[:100]}... | Commented by: {self.comment_by.full_name()}"


class InviteCollaborators(BaseModel):
    STATUS_CHOICES = (
        ("accepted", "accepted"),
        ("pending", "pending"),
        ("decline", "decline"),
    )
    co_author = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="invited_co_author",
    )
    invited_by = models.ForeignKey(
        "authentication.User", on_delete=models.CASCADE, related_name="invited_by_user"
    )
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default="pending")

    class Meta:
        db_table = "invite_collaborators"
        verbose_name = "Invite Collaborators"
        verbose_name_plural = "Invite Collaborators"

    def __str__(self):
        return (
            f"{self.co_author.full_name()} was invited by {self.invited_by.full_name()}"
        )
