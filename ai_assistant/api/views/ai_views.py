import requests

from django.conf import settings
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse

from base.constants.verification import VerificationStatus
from base.constants.ai_query_types import QueryType

from ai_assistant.models import AIQueryHistory
from cases.models import CaseCategory
from lawyers.models import Lawyer
from firms.models import Firm
from lawyers.api.serializers import LawyerPublicSerializer
from firms.api.serializers import FirmPublicSerializer
from ai_assistant.services.ai_services import call_ai_service

AI_SERVICE_URL = settings.AI_SERVICE_URL

class AIQueryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Ask AI legal assistant",
        description="Authenticated endpoint to ask legal questions and receive AI-assisted responses.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        },
        responses={
            200: OpenApiResponse(description="AI response"),
            400: OpenApiResponse(description="Invalid input"),
            503: OpenApiResponse(description="AI service unavailable"),
        },
        tags=["ai-assistant"],
    )
    @transaction.atomic
    def post(self, request):
        query = request.data.get("query")

        if not query:
            return Response(
                {"error": "Query is required"},
                status=400
            )

        try:
            ai_data = call_ai_service(
                {
                    "question": query,
                    "user_id": str(request.user.id),
                }
            )
        except requests.RequestException:
            return Response(
                {"error": "AI service unavailable"},
                status=503
            )
    
        answer = ai_data.get("answer", "")
        raw_query_type = ai_data.get("query_type", "")
        query_type = raw_query_type.strip().lower().split()[0]
        case_category_name = ai_data.get("case_category") or None

        # 2️⃣ Store base history
        history = AIQueryHistory.objects.create(
            user=request.user,
            query=query,
            query_type=query_type,
            answer=answer,
            raw_ai_response=ai_data,
        )

        response_payload = {
            "answer": answer,
            "query_type": query_type,
            "recommendations": [],
        }

        # 3️⃣ Handle recommendations ONLY when AI explicitly says so
        if (
            query_type == QueryType.RECOMMENDATION
            and case_category_name
        ):
            case_category = CaseCategory.objects.filter(
                name__iexact=case_category_name
            ).first()

            if case_category:
                history.case_category = case_category
                history.save(update_fields=["case_category"])

                # 🔹 Fetch VERIFIED lawyers
                lawyers = (
                    Lawyer.objects
                    .filter(
                        services=case_category,
                        user__bar_verification__status=VerificationStatus.VERIFIED,
                    )
                    .select_related("user", "address", "user__bar_verification")
                    .prefetch_related("services")
                    .distinct()[:5]
                )

                # 🔹 Fetch VERIFIED firms
                firms = (
                    Firm.objects
                    .filter(
                        services=case_category,
                        user__firm_verification__status=VerificationStatus.VERIFIED,
                    )
                    .select_related("user", "address", "user__firm_verification")
                    .prefetch_related("services")
                    .distinct()[:5]
                )

                # 🔹 Persist recommendations
                history.recommended_lawyers.set(lawyers)
                history.recommended_firms.set(firms)

                response_payload["recommendations"] = {
                    "case_category": case_category.name,
                    "lawyers": LawyerPublicSerializer(
                        [
                            {
                                "user": l.user,
                                "profile": l,
                                "verification": l.user.bar_verification,
                            }
                            for l in lawyers
                        ],
                        many=True,
                    ).data,
                    "firms": FirmPublicSerializer(
                        [
                            {
                                "user": f.user,
                                "profile": f,
                                "verification": f.user.firm_verification,
                            }
                            for f in firms
                        ],
                        many=True,
                    ).data,
                }

        return Response(response_payload, status=200)
