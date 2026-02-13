from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser

from drf_spectacular.utils import extend_schema

from media.models import Image
from media.services.cloudinary_service import CloudinaryService


class ImageUploadView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Upload image",
        description="Upload an image file and return its ID and URL.",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                    }
                },
                "required": ["file"],
            }
        },
        responses={201: dict},
        tags=["media"],
    )
    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "file is required"}, status=400)

        upload_result = CloudinaryService.upload_file(
            file,
            folder="trilex/uploads"
        )

        image = Image.objects.create(url=upload_result["url"])

        return Response(
            {
                "id": image.id,
                "url": image.url,
            },
            status=201
        )
