from rest_framework import serializers

from .models import Resume


class ResumeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Resume
        fields = [
            "id",
            "file",
            "uploaded_at",
            "is_analyzed",
        ]

        read_only_fields = [
            "id",
            "uploaded_at",
            "is_analyzed",
        ]