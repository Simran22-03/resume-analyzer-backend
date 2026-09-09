from rest_framework import serializers
from django.contrib.auth import get_user_model


User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "email",
            "password",
            "role",
            "company_name",
        ]

    def validate(self, data):
        role = data.get("role")
        company = data.get("company_name")

        if role == "hr" and not company:
            raise serializers.ValidationError({
                "company_name": "Company name is required for HR."
            })

        if role == "employee":
            data["company_name"] = None

        return data

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user