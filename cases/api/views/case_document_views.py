# cases/api/views/case_document.py
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from cases.models import Case, CaseDocument
from cases.api.serializers import (
    CaseDocumentCreateSerializer,
    CaseDocumentSerializer,
)
from cases.permissions import CanUploadCaseDocument, CanViewCaseDocuments
from base.constants.user_roles import UserRoles

class CaseDocumentCreateView(APIView):
    permission_classes = [IsAuthenticated, CanUploadCaseDocument]

    def post(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        serializer = CaseDocumentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if user.role == UserRoles.CLIENT:
            uploaded_by = "client"
        elif user.role == UserRoles.FIRM:
            uploaded_by = "firm"
        else:
            uploaded_by = "lawyer"

        doc = CaseDocument.objects.create(
            case=case,
            uploaded_by_type=uploaded_by,
            uploaded_by_user=user,
            **serializer.validated_data
        )

        return Response(
            CaseDocumentSerializer(doc).data,
            status=201
        )

class CaseDocumentListView(APIView):
    permission_classes = [IsAuthenticated, CanViewCaseDocuments]

    def get(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        qs = case.documents.all()

        if request.user == case.client_user:
            qs = qs.filter(uploaded_by_type="client")

        serializer = CaseDocumentSerializer(qs, many=True)
        return Response(serializer.data)
