import base64
import secrets
import string
from datetime import datetime
from typing import Optional, List, Any

import cloudinary
import cloudinary.uploader
import httpx
from asgiref.sync import sync_to_async
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string

from blendjoy import settings
from blendjoy.settings import env


class UploadFilesToCloudinary:

    def __init__(self) -> None:
        cloud_name = env("CLOUDINARY_CLOUD_NAME")
        api_key = env("CLOUDINARY_API_KEY")
        secret_key = env("CLOUDINARY_SECRET_KEY")
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=secret_key,
            secure=True,
        )

    @classmethod
    def upload_file(
        cls,
        file_path: str,
        public_id: str,
        folder: Optional[str] = None,
        transformation: Optional[List[dict[str, Any]]] = None,
    ):
        upload_result = cloudinary.uploader.upload(
            file_path, public_id=public_id, folder=folder, transformation=transformation
        )
        return upload_result

    @classmethod
    def delete_file(cls, public_id: str):
        cloudinary.uploader.destroy(public_id)

    @classmethod
    def upload_multiple_files(
        cls,
        files: List["InMemoryUploadedFile"],
        folder: Optional[str] = None,
        transformation: Optional[List[dict[str, Any]]] = None,
    ) -> List[dict[str, Any]]:
        """
        Upload multiple files to Cloudinary.

        Args:
            files (List[InMemoryUploadedFile]): List of InMemoryUploadedFile objects to upload.
            folder (Optional[str]): Cloudinary folder where files will be uploaded.
            transformation (Optional[List[dict[str, Any]]]): Optional transformation parameters for the files.

        Returns:
            List[dict[str, Any]]: List of results from Cloudinary for each upload.
        """
        upload_results = []

        for idx, file in enumerate(files):
            try:
                # Extract the original filename from the InMemoryUploadedFile object
                filename = file.name
                public_id = (
                    f"{folder}/{filename.split('.')[0]}_{idx}"
                    if folder
                    else f"{filename.split('.')[0]}_{idx}"
                )
                resource_type = (
                    "video" if file.content_type.startswith("video/") else "image"
                )
                # Upload the file directly from memory (Django's InMemoryUploadedFile)
                result = cloudinary.uploader.upload(
                    file,
                    public_id=public_id,
                    folder=folder,
                    transformation=transformation,
                    resource_type=resource_type,
                )
                upload_results.append(result)
            except Exception as e:
                upload_results.append({"error": str(e)})
                continue

        return upload_results


def natural_time(value):
    return naturaltime(value)


class AsyncHttpxSingleton:
    _instance = None

    @classmethod
    async def get_instance(cls):
        if cls._instance is None or cls._instance.is_closed:
            cls._instance = httpx.AsyncClient()
            print("Creating new instance for httpx.AsyncClient()")
        else:
            print("Reusing existing instance for httpx.AsyncClient()")
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance and not cls._instance.is_closed:
            await cls._instance.aclose()
        cls._instance = None


async def plagiarism_checker(text: str):
    API_TOKEN = env("PLAGIARISM_CHECK_API_TOKEN")
    headers = {"X-API-TOKEN": API_TOKEN}
    url = "https://plagiarismcheck.org/api/v1/text"

    data = {"language": "en", "text": text}

    response = httpx.post(url=url, data=data, headers=headers)
    return response.json()


async def get_plagiarism_checker_report(log_id):
    API_TOKEN = env("PLAGIARISM_CHECK_API_TOKEN")
    headers = {"X-API-TOKEN": API_TOKEN}
    url = f"https://plagiarismcheck.org/api/v1/text/report/{log_id}"
    response = httpx.get(url=url, headers=headers)
    return response.json()


def send_email_verification(email):
    subject = "Email Verification Link"

    email_bytes = email.encode("ascii")

    base64_bytes = base64.b64encode(email_bytes)
    base64_string = base64_bytes.decode("ascii")

    # Render the HTML email templates
    message = render_to_string(
        "email_verification.html",
        {
            "email": email,
            "verification_link": f"https://readify.fun/verify-email/{base64_string}",
        },
    )

    # Create email message object
    email_message = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [email])

    # Specify that the content is HTML
    email_message.content_subtype = "html"

    # Send the email
    email_message.send()


def encrypt_str(text):
    base64_bytes = text.encode("ascii")

    sample_string_bytes = base64.b64decode(base64_bytes)
    decoded_text = sample_string_bytes.decode("ascii")

    return decoded_text


def generate_random_password(length=12):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(alphabet) for _ in range(length))


def calculate_age_from_string(date_string):
    # Convert the string to a datetime object
    birthdate = datetime.strptime(date_string, "%Y-%m-%d")

    # Get the current date
    today = datetime.today()

    # Calculate the age
    age = today.year - birthdate.year

    # Adjust if the birthdate hasn't occurred yet this year
    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1

    return age


def send_password_reset_verification(email):
    subject = "Password Reset Link"

    email_bytes = email.encode("ascii")

    base64_bytes = base64.b64encode(email_bytes)
    base64_string = base64_bytes.decode("ascii")

    # Render the HTML email templates
    message = render_to_string(
        "password_reset_email.html",
        {
            "email": email,
            "verification_link": f"https://readify.fun/reset-password/{base64_string}",
        },
    )

    # Create email message object
    email_message = EmailMessage(subject, message, settings.EMAIL_HOST_USER, [email])

    # Specify that the content is HTML
    email_message.content_subtype = "html"

    # Send the email
    email_message.send()
