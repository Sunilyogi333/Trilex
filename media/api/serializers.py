# media/api/serializers.py

from rest_framework import serializers
from media.models import Image


class ImageUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ("id", "url")
