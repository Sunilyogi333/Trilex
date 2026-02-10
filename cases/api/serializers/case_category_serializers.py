from rest_framework import serializers
from cases.models import CaseCategory

class CaseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseCategory
        fields = ["id", "name", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]
