from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from cases.models import CaseCategory
from .serializers import CaseCategorySerializer
from cases.services.services import CaseCategoryService
from accounts.permissions import IsAdminUser

class CaseCategoryListCreateAPIView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdminUser()]
        return [AllowAny()]

    def get(self, request):
        categories = CaseCategoryService.get_all_categories(
            active_only=request.query_params.get("active") == "true"
        )
        serializer = CaseCategorySerializer(categories, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=CaseCategorySerializer,
        responses={201: CaseCategorySerializer},
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


from rest_framework.permissions import AllowAny


class CaseCategoryDetailAPIView(APIView):

    def get_permissions(self):
        if self.request.method in ["PUT", "DELETE"]:
            return [IsAdminUser()]
        return [AllowAny()]

    def get(self, request, pk):
        category = get_object_or_404(CaseCategory, pk=pk)
        serializer = CaseCategorySerializer(category)
        return Response(serializer.data)

    @extend_schema(
        request=CaseCategorySerializer,
        responses={200: CaseCategorySerializer},
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

    def delete(self, request, pk):
        category = get_object_or_404(CaseCategory, pk=pk)
        CaseCategoryService.delete_category(category)
        return Response(status=status.HTTP_204_NO_CONTENT)
