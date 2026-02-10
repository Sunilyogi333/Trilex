# cases/api/views/case_date.py
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from cases.models import Case, CaseDate
from cases.api.serializers import (
    CaseDateCreateSerializer,
    CaseDateSerializer,
)
from cases.permissions import CanManageCaseDates

class CaseDateCreateView(APIView):
    permission_classes = [IsAuthenticated, CanManageCaseDates]

    def post(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        serializer = CaseDateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        date = CaseDate.objects.create(
            case=case,
            **serializer.validated_data
        )

        return Response(
            CaseDateSerializer(date).data,
            status=201
        )

