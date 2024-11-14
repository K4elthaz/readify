from typing import List, Any


from asgiref.sync import sync_to_async
from cloudinary import CloudinaryImage
from django.http import JsonResponse

from app.social_newsfeed.models import SocialPost
from app.utils import UploadFilesToCloudinary


@sync_to_async
def new_post(request):
    if request.method == "POST":
        user = request.user
        files = request.FILES.getlist("files[]")
        caption = request.POST.get("caption", "")

        folder: str = "social_medias"

        uploaded_files = []

        if len(files) > 0:
            init_cloudinary: UploadFilesToCloudinary = UploadFilesToCloudinary()
            transformation: List[dict[str, Any]] = [{"width": 200, "height": 200}]

            uploaded_files = init_cloudinary.upload_multiple_files(
                files, folder, transformation=transformation
            )

        SocialPost.objects.create(author=user, caption=caption, media=uploaded_files)

        response = JsonResponse({"message": "Social posts created successfully"})
        response["HX-Redirect"] = f"/social"
        return response


def delete_social_post_service(request, id):
    user = request.user
    SocialPost.objects.filter(id=id).delete()
    response = JsonResponse({"message": "Social posts created successfully"})
    response["HX-Redirect"] = f"/profile/{user.id}"
    return response
