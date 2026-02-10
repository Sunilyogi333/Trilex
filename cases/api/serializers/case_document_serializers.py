from rest_framework import serializers

from cases.models import CaseDocument
from media.models import Image
from media.api.serializers import ImageSerializer

class CaseDocumentCreateSerializer(serializers.ModelSerializer):
    file = serializers.PrimaryKeyRelatedField(
        queryset=Image.objects.all()
    )

    class Meta:
        model = CaseDocument
        fields = (
            "title",
            "description",
            "file",
            "file_type",
        )

class CaseDocumentSerializer(serializers.ModelSerializer):
    file = ImageSerializer(read_only=True)

    class Meta:
        model = CaseDocument
        fields = (
            "id",
            "title",
            "description",
            "file",
            "file_type",
            "uploaded_by_type",
            "uploaded_by_user",
            "created_at",
        )
