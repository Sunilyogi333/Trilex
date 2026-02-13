import os
import cloudinary.uploader


class CloudinaryService:

    @staticmethod
    def upload_file(file, folder: str = "trilex"):
        """
        Dynamically detect resource type based on file extension.
        """

        extension = os.path.splitext(file.name)[1].lower()

        if extension in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            resource_type = "image"
        elif extension in [".mp4", ".mov", ".avi"]:
            resource_type = "video"
        else:
            resource_type = "raw"

        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type=resource_type
        )

        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
        }
