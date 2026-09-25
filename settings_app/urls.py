from django.urls import path

from .views import (
    UserProfileView,
    ChangePasswordView,
)


urlpatterns = [

    # =========================================================
    # PROFILE
    # =========================================================

    path("profile/",UserProfileView.as_view(),name="settings-profile",),

    # =========================================================
    # CHANGE PASSWORD
    # =========================================================

    path("change-password/",ChangePasswordView.as_view(),name="settings-change-password",),
]