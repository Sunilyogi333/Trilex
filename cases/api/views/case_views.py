# cases/api/views/case.py
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from base.constants.user_roles import UserRoles
from cases.models import Case, CaseLawyer
from cases.api.serializers import (
    CaseCreateSerializer,
    CaseUpdateSerializer,
    CaseDetailSerializer,
)
from cases.permissions import CanViewCase, CanEditCase
from lawyers.models import Lawyer
from firms.models import Firm

class CaseCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        data = serializer.validated_data

        if user.role == UserRoles.LAWYER:
            lawyer = Lawyer.objects.get(user=user)

            case = Case.objects.create(
                owner_type="lawyer",
                owner_lawyer=lawyer,
                created_by=user,
                **data
            )

            CaseLawyer.objects.create(
                case=case,
                lawyer=lawyer,
                role="lead",
                can_edit=True,
            )

        elif user.role == UserRoles.FIRM:
            firm = Firm.objects.get(user=user)

            case = Case.objects.create(
                owner_type="firm",
                owner_firm=firm,
                created_by=user,
                **data
            )
        else:
            return Response({"error": "Not allowed"}, status=403)

        return Response(
            CaseDetailSerializer(case).data,
            status=201
        )

class CaseDetailView(APIView):
    permission_classes = [IsAuthenticated, CanViewCase]

    def get(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        return Response(CaseDetailSerializer(case).data)

class CaseUpdateView(APIView):
    permission_classes = [IsAuthenticated, CanEditCase]

    def patch(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        serializer = CaseUpdateSerializer(
            case, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            CaseDetailSerializer(case).data
        )

