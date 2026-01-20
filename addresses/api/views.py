# addresses/api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from drf_spectacular.utils import extend_schema

from addresses.models.province import Province
from addresses.models.district import District
from addresses.models.municipality import Municipality
from addresses.models.ward import Ward

from addresses.api.serializers import (
    ProvinceSerializer,
    DistrictSerializer,
    MunicipalitySerializer,
    WardSerializer,
)


# =========================
# PROVINCE
# =========================

class ProvinceListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List provinces",
        description="Returns all provinces of Nepal.",
        responses={200: ProvinceSerializer(many=True)},
        tags=["addresses"],
    )
    def get(self, request):
        qs = Province.objects.all().order_by("code")
        serializer = ProvinceSerializer(qs, many=True)
        return Response(serializer.data)


# =========================
# DISTRICT
# =========================

class DistrictListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List districts by province",
        description="Returns districts belonging to a province.",
        responses={200: DistrictSerializer(many=True)},
        tags=["addresses"],
    )
    def get(self, request, province_id):
        qs = District.objects.filter(
            province_id=province_id
        ).select_related("province")
        serializer = DistrictSerializer(qs, many=True)
        return Response(serializer.data)


# =========================
# MUNICIPALITY
# =========================

class MunicipalityListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List municipalities by district",
        description="Returns municipalities belonging to a district.",
        responses={200: MunicipalitySerializer(many=True)},
        tags=["addresses"],
    )
    def get(self, request, district_id):
        qs = Municipality.objects.filter(
            district_id=district_id
        ).select_related("district", "district__province")
        serializer = MunicipalitySerializer(qs, many=True)
        return Response(serializer.data)


# =========================
# WARD
# =========================

class WardListView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="List wards by municipality",
        description="Returns wards belonging to a municipality.",
        responses={200: WardSerializer(many=True)},
        tags=["addresses"],
    )
    def get(self, request, municipality_id):
        qs = Ward.objects.filter(
            municipality_id=municipality_id
        ).select_related(
            "municipality",
            "municipality__district",
            "municipality__district__province",
        )
        serializer = WardSerializer(qs, many=True)
        return Response(serializer.data)
