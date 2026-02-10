# cases/api/views/case_lawyer.py
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from cases.models import Case, CaseLawyer
from cases.api.serializers import CaseLawyerAssignSerializer
from cases.permissions import CanAssignCaseLawyers
from firms.models import FirmMember

class CaseLawyerAssignView(APIView):
    permission_classes = [IsAuthenticated, CanAssignCaseLawyers]

    def post(self, request, case_id):
        case = get_object_or_404(Case, id=case_id)
        self.check_object_permissions(request, case)

        serializer = CaseLawyerAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        lawyer = serializer.validated_data["lawyer"]

        # ensure lawyer belongs to firm
        FirmMember.objects.get(
            firm=case.owner_firm,
            lawyer=lawyer
        )

        CaseLawyer.objects.create(
            case=case,
            lawyer=lawyer,
            role=serializer.validated_data.get("role", "assistant"),
            can_edit=serializer.validated_data.get("can_edit", True),
        )

        return Response({"message": "Lawyer assigned"}, status=201)

