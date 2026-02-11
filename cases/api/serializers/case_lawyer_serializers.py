from rest_framework import serializers
from lawyers.models import Lawyer


class CaseLawyerAssignSerializer(serializers.Serializer):
    lawyer = serializers.PrimaryKeyRelatedField(
        queryset=Lawyer.objects.all()
    )
