# addresses/api/serializers.py

from rest_framework import serializers

from addresses.models.address import Address
from addresses.models.province import Province
from addresses.models.district import District
from addresses.models.municipality import Municipality
from addresses.models.ward import Ward


# =========================
# READ-ONLY SERIALIZERS
# =========================

class ProvinceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Province
        fields = ["id", "title", "title_nepali", "code"]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "title", "title_nepali", "code"]


class MunicipalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Municipality
        fields = ["id", "title", "title_nepali", "code"]


class WardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ward
        fields = ["id", "number", "number_nepali"]


# =========================
# ADDRESS SERIALIZERS
# =========================

class AddressInputSerializer(serializers.Serializer):
    """
    Used when creating/updating address
    (IDs only, validated in service layer)
    """
    province = serializers.IntegerField()
    district = serializers.IntegerField()
    municipality = serializers.IntegerField()
    ward = serializers.IntegerField()


class AddressSerializer(serializers.ModelSerializer):
    """
    Fully expanded address response
    """
    province = ProvinceSerializer(read_only=True)
    district = DistrictSerializer(read_only=True)
    municipality = MunicipalitySerializer(read_only=True)
    ward = WardSerializer(read_only=True)

    class Meta:
        model = Address
        fields = [
            "id",
            "province",
            "district",
            "municipality",
            "ward",
            "created_at",
            "updated_at",
        ]
