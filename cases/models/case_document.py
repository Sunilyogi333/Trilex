from django.conf import settings
from django.db import models

from base.models import AbstractBaseModel
from cases.models.case import Case
from media.models import Image
from base.constants.case import CaseDocumentFileType, CaseDocumentUploader, CaseDocumentScope

User = settings.AUTH_USER_MODEL

class CaseDocument(AbstractBaseModel):
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="documents"
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    file = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name="case_documents"
    )

    file_type = models.CharField(
        max_length=20,
        choices=CaseDocumentFileType.choices
    )

    document_scope = models.CharField(
    max_length=20,
    choices=CaseDocumentScope.choices,
    default=CaseDocumentScope.INTERNAL
)


    uploaded_by_type = models.CharField(
        max_length=20,
        choices=CaseDocumentUploader.choices
    )

    uploaded_by_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_case_documents"
    )

    def __str__(self):
        return f"Document({self.title})"
