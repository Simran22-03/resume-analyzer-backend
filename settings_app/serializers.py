from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(
        source="first_name",
        required=True,
        allow_blank=False,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
        ]
        read_only_fields = [
            "id",
        ]

    def validate_email(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Email address is required."
            )

        queryset = User.objects.filter(
            email__iexact=value
        ).exclude(
            pk=self.instance.pk
        )

        if queryset.exists():
            raise serializers.ValidationError(
                "This email address is already in use."
            )

        return value


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        required=True,
        write_only=True,
    )

    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
    )

    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
    )

    def validate(self, attrs):
        user = self.context["request"].user

        current_password = attrs[
            "current_password"
        ]

        new_password = attrs[
            "new_password"
        ]

        confirm_password = attrs[
            "confirm_password"
        ]

        if not user.check_password(
            current_password
        ):
            raise serializers.ValidationError(
                {
                    "current_password":
                        "Current password is incorrect."
                }
            )

        if new_password != confirm_password:
            raise serializers.ValidationError(
                {
                    "confirm_password":
                        "New password and confirm password do not match."
                }
            )

        if user.check_password(
            new_password
        ):
            raise serializers.ValidationError(
                {
                    "new_password":
                        "New password must be different from your current password."
                }
            )

        return attrs