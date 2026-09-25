from django.contrib.auth import update_session_auth_hash

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    UserProfileSerializer,
    ChangePasswordSerializer,
)


# =========================================================
# PROFILE
# =========================================================

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(
            request.user
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True,
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()

        return Response(
            {
                "message": "Profile updated successfully.",
                "profile": UserProfileSerializer(
                    user
                ).data,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# CHANGE PASSWORD
# =========================================================

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user

        user.set_password(
            serializer.validated_data[
                "new_password"
            ]
        )

        user.save(
            update_fields=[
                "password",
            ]
        )

        # Keep the current Django session valid.
        # Our frontend will handle JWT logout/re-login
        # after the password change.
        update_session_auth_hash(
            request,
            user,
        )

        return Response(
            {
                "message": (
                    "Password updated successfully."
                )
            },
            status=status.HTTP_200_OK,
        )