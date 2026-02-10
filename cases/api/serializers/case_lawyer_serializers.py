from rest_framework import serializers

from cases.models import CaseLawyer
from lawyers.models import Lawyer

class CaseLawyerAssignSerializer(serializers.Serializer):
    lawyer = serializers.PrimaryKeyRelatedField(
        queryset=Lawyer.objects.all()
    )

    role = serializers.ChoiceField(
        choices=CaseLawyer._meta.get_field("role").choices,
        required=False
    )

    can_edit = serializers.BooleanField(required=False)
