from rest_framework import serializers

from cases.models import CaseDocument
from media.models import Image
from media.api.serializers import ImageSerializer
from base.constants.case import CaseDocumentScope


class CaseDocumentCreateSerializer(serializers.ModelSerializer):
    file = serializers.PrimaryKeyRelatedField(
        queryset=Image.objects.all()
    )

    document_scope = serializers.ChoiceField(
        choices=CaseDocumentScope.choices,
        default=CaseDocumentScope.INTERNAL
    )

    class Meta:
        model = CaseDocument
        fields = (
            "title",
            "description",
            "file",
            "file_type",
            "document_scope",
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
            "document_scope",
            "uploaded_by_type",
            "uploaded_by_user",
            "created_at",
        )
