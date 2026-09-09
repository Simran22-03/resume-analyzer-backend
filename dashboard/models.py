from django.conf import settings
from django.db import models


class Resume(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="resumes",
    )

    file = models.FileField(
        upload_to="resumes/"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    is_analyzed = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.user.email} - {self.file.name}"


class ResumeAnalysis(models.Model):

    resume = models.OneToOneField(
        Resume,
        on_delete=models.CASCADE,
        related_name="analysis",
    )

    job_description = models.TextField()

    ats_score = models.PositiveIntegerField(
        default=0
    )

    skills = models.JSONField(
        default=list,
        blank=True
    )

    strengths = models.JSONField(
        default=list,
        blank=True
    )

    weaknesses = models.JSONField(
        default=list,
        blank=True
    )

    missing_skills = models.JSONField(
        default=list,
        blank=True
    )

    suggestions = models.JSONField(
        default=list,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Analysis - {self.resume.file.name}"


class ChatHistory(models.Model):

    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="copilot_messages",
    )

    resume = models.ForeignKey(
        Resume,
        on_delete=models.CASCADE,
        related_name="copilot_messages",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
    )

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["created_at"]

        indexes = [
            models.Index(
                fields=[
                    "user",
                    "resume",
                    "created_at",
                ]
            )
        ]

    def __str__(self):
        return (
            f"{self.user.email} - "
            f"Resume {self.resume_id} - "
            f"{self.role}"
        )