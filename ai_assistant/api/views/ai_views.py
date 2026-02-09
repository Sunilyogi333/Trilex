from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import extend_schema, OpenApiResponse

from base.constants.user_roles import UserRoles
from base.constants.verification import VerificationStatus
from base.constants.ai_query_types import QueryType

from accounts.permissions import IsVerifiedClientLawyerOrFirm

from ai_assistant.models import AIQueryHistory
from ai_assistant.services.ai_services import call_ai_service

from cases.models import CaseCategory
from lawyers.models import Lawyer
from firms.models import Firm
from lawyers.api.serializers import LawyerPublicSerializer
from firms.api.serializers import FirmPublicSerializer
from base.pagination import DefaultPageNumberPagination

class AIQueryView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsVerifiedClientLawyerOrFirm,
    ]

    @extend_schema(
        summary="Ask AI legal assistant",
        description="Verified users can ask legal questions. Only clients receive lawyer/firm recommendations.",
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
    def post(self, request):
        query = request.data.get("query")

        if not query:
            return Response({"error": "Query is required"}, status=400)

        # 🔐 Role context
        user_role = request.user.role
        is_client = user_role == UserRoles.CLIENT

        # 1️⃣ Call AI service with ROLE
        try:
            ai_data = call_ai_service(
                {
                    "question": query,
                    "user_id": str(request.user.id),
                    "user_role": user_role,
                }
            )
        except Exception:
            return Response(
                {"error": "AI service unavailable"},
                status=503
            )

        # 2️⃣ Normalize AI response
        answer = ai_data.get("answer", "")
        raw_query_type = ai_data.get("query_type", "")
        query_type = raw_query_type.strip().lower().split()[0]
        case_category_name = ai_data.get("case_category") or None

        # 3️⃣ Store history
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
            "created_at": history.created_at,

        }

        # 4️⃣ Recommendation logic (CLIENT ONLY)
        if (
            is_client
            and query_type == QueryType.RECOMMENDATION
            and case_category_name
        ):
            case_category = CaseCategory.objects.filter(
                name__iexact=case_category_name
            ).first()

            if case_category:
                history.case_category = case_category
                history.save(update_fields=["case_category"])

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

class AIQueryHistoryListView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsVerifiedClientLawyerOrFirm,
    ]

    @extend_schema(
        summary="Get my AI chat history",
        description="Returns AI query history in chat-style flattened message format.",
        responses={200: OpenApiResponse(description="Chat history")},
        tags=["ai-assistant"],
    )
    def get(self, request):
        qs = (
            AIQueryHistory.objects
            .filter(user=request.user)
            .select_related("case_category")
            .prefetch_related(
                "recommended_lawyers__user__bar_verification",
                "recommended_firms__user__firm_verification",
            )
            .order_by("created_at")
        )

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(qs, request)

        messages = []

        for history in page:
            # 🧑 USER MESSAGE
            messages.append({
                "sender": "user",
                "message": history.query,
                "created_at": history.created_at,
            })

            # 🤖 AI MESSAGE
            ai_message = {
                "sender": "ai",
                "message": history.answer or "",
                "query_type": history.query_type,
                "recommendations": [],
                "created_at": history.created_at,
            }

            # Only CLIENT recommendation messages have recommendations
            if (
                history.query_type == QueryType.RECOMMENDATION
                and history.case_category
            ):
                ai_message["recommendations"] = {
                    "case_category": history.case_category.name,
                    "lawyers": LawyerPublicSerializer(
                        [
                            {
                                "user": l.user,
                                "profile": l,
                                "verification": l.user.bar_verification,
                            }
                            for l in history.recommended_lawyers.all()
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
                            for f in history.recommended_firms.all()
                        ],
                        many=True,
                    ).data,
                }

            messages.append(ai_message)

        return paginator.get_paginated_response(messages)
