from django.contrib import admin
from .models import ChatHistory, Resume, ResumeAnalysis


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "resume",
        "role",
        "message",
        "created_at",
    )

    list_filter = (
        "role",
        "created_at",
    )

    search_fields = (
        "user__email",
        "message",
    )

    ordering = (
        "-created_at",
    )


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "file",
        "uploaded_at",
        "is_analyzed",
    )

    list_filter = (
        "is_analyzed",
        "uploaded_at",
    )


@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "resume",
        "ats_score",
        "created_at",
    )