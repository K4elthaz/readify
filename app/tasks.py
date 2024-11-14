import json

from asgiref.sync import async_to_sync
from bs4 import BeautifulSoup
from celery import shared_task
from django.shortcuts import get_object_or_404

from app.authentication.models import FollowedAuthor
from app.notifications.views.services import save_notifications
from app.utils import plagiarism_checker, get_plagiarism_checker_report
from app.books.models import BooksChapter, PlagiarismCheckerLogs, Books


@shared_task
def run_plagiarism_checker_tasks(slug):
    print("Running plagiarism checker ...")

    chapter = get_object_or_404(BooksChapter, slug=slug)

    soup = BeautifulSoup(chapter.content, "html.parser")
    # Get text from the parsed HTML
    content = soup.get_text(separator="\n", strip=True)
    checker = async_to_sync(plagiarism_checker)(text=content)

    print("Saving plagiarism checker results ...")
    PlagiarismCheckerLogs.objects.create(
        book=chapter.book,
        chapter=chapter,
        results=checker,
        log_id=checker["data"]["text"]["id"],
        words_count=checker["data"]["text"]["words"],
    )

    print("Done saving plagiarism checker results ...")


@shared_task
def run_plagiarism_report_tasks(slug):
    print("Retrieving plagiarism checker reports ...")

    # Retrieve the book based on the slug
    book = get_object_or_404(Books, slug=slug)

    # Filter logs for the given book
    logs = PlagiarismCheckerLogs.objects.filter(book=book)

    # Prepare new logs for bulk update
    new_logs = []

    for log in logs:
        chapter = log.chapter
        log_id = log.log_id

        # Retrieve the plagiarism checker report asynchronously
        report = async_to_sync(get_plagiarism_checker_report)(log_id=log_id)

        # Update the log instance with the new results
        log.results = report  # Assuming `results` is a field on PlagiarismCheckerLogs
        new_logs.append(log)  # Append the log instance itself

    print("Saving plagiarism checker reports ...")
    # Perform a bulk update on the modified log instances
    PlagiarismCheckerLogs.objects.bulk_update(
        new_logs, ["results"]
    )  # Specify fields to update

    notification_message = f"""
        <p class="text-sm font-semibold text-gray-900">Your Plagiarism Report is Ready!</p>
        <hr>
        <p class="mt-2 text-xs text-gray-500">
            You can access your plagiarism checker report <a href="/books/plagiarism/{slug}" class="text-pink-500 underline">by
            clicking here</a>.
        </p>
    """
    save_notifications(user=book.author, message=notification_message)
    print("Done retrieving plagiarism checker reports ...")
