from rest_framework import serializers


class FirmDashboardSerializer(serializers.Serializer):
    total_cases = serializers.IntegerField()
    total_ongoing_cases = serializers.IntegerField()
    total_pending_bookings = serializers.IntegerField()
    total_members = serializers.IntegerField()
    cases_per_month = serializers.ListField(
        child=serializers.DictField()
    )
