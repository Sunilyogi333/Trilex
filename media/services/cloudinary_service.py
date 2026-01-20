# media/services/cloudinary_service.py

import cloudinary.uploader
import cloudinary.api


class CloudinaryService:
    """
    Handles Cloudinary uploads & deletions.
    """

    @staticmethod
    def upload_image(file, folder: str = "trilex"):
        """
        Uploads file to Cloudinary.

        Returns:
            {
                "url": secure_url,
                "public_id": public_id
            }
        """
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type="image"
        )

        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
        }

    @staticmethod
    def delete_image(public_id: str):
        """
        Deletes image from Cloudinary.
        """
        cloudinary.uploader.destroy(
            public_id,
            resource_type="image"
        )
