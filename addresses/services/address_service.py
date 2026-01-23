from rest_framework.exceptions import ValidationError
from addresses.models import (
    Province, District, Municipality, Ward, Address
)

class AddressService:

    @staticmethod
    def validate(data):
        try:
            province = Province.objects.get(id=data["province"])
            district = District.objects.get(id=data["district"], province=province)
            municipality = Municipality.objects.get(id=data["municipality"], district=district)
            ward = Ward.objects.get(id=data["ward"], municipality=municipality)
        except Exception:
            return None

        return {
            "province": province,
            "district": district,
            "municipality": municipality,
            "ward": ward,
        }

    @staticmethod
    def create(data):
        validated = AddressService.validate(data)
        if not validated:
            raise ValidationError("Invalid address hierarchy")

        return Address.objects.create(**validated)
