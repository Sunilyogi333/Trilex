from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from cases.models import CaseCategory
from cases.api.serializers.case_category_serializers import CaseCategorySerializer
from cases.services.services import CaseCategoryService
from accounts.permissions import IsAdminUser
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)

from base.pagination import DefaultPageNumberPagination


class CaseCategoryListCreateAPIView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [AllowAny()]

    @extend_schema(
        summary="List case categories",
        description=(
            "Returns a paginated list of case categories. "
            "Public users can view all active categories. "
            "Admins can view both active and inactive categories."
        ),
        parameters=[
            OpenApiParameter(
                name="active",
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Filter only active categories (true/false)",
            ),
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Page number",
            ),
            OpenApiParameter(
                name="page_size",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of items per page",
            ),
        ],
        responses={
            200: CaseCategorySerializer(many=True)
        },
        tags=["cases"],
    )
    def get(self, request):
        categories = CaseCategoryService.get_all_categories(
            active_only=request.query_params.get("active") == "true"
        )

        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(categories, request)

        serializer = CaseCategorySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


    @extend_schema(
        summary="Create case category",
        description="Admin-only endpoint to create a new case category.",
        request=CaseCategorySerializer,
        responses={
            201: CaseCategorySerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Forbidden"),
        },
        tags=["cases"],
    )
    def post(self, request):
        serializer = CaseCategorySerializer(data=request.data)
        if serializer.is_valid():
            category = CaseCategoryService.create_category(
                serializer.validated_data
            )
            return Response(
                CaseCategorySerializer(category).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CaseCategoryDetailAPIView(APIView):

    def get_permissions(self):
        if self.request.method in ["PUT", "DELETE"]:
            return [IsAdminUser()]
        return [AllowAny()]

    @extend_schema(
        summary="Get case category details",
        description="Retrieve a single case category by ID.",
        responses={200: CaseCategorySerializer},
        tags=["cases"],
    )
    def get(self, request, pk):
        category = get_object_or_404(CaseCategory, pk=pk)
        serializer = CaseCategorySerializer(category)
        return Response(serializer.data)

    @extend_schema(
        summary="Update case category",
        description="Admin-only endpoint to update a case category.",
        request=CaseCategorySerializer,
        responses={
            200: CaseCategorySerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Forbidden"),
        },
        tags=["cases"],
    )
    def put(self, request, pk):
        category = get_object_or_404(CaseCategory, pk=pk)
        serializer = CaseCategorySerializer(
            category, data=request.data, partial=True
        )
        if serializer.is_valid():
            category = CaseCategoryService.update_category(
                category, serializer.validated_data
            )
            return Response(
                CaseCategorySerializer(category).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete case category",
        description="Admin-only endpoint to delete a case category.",
        responses={
            204: OpenApiResponse(description="Deleted successfully"),
            403: OpenApiResponse(description="Forbidden"),
        },
        tags=["cases"],
    )
    def delete(self, request, pk):
        category = get_object_or_404(CaseCategory, pk=pk)
        CaseCategoryService.delete_category(category)
        return Response(status=status.HTTP_204_NO_CONTENT)

