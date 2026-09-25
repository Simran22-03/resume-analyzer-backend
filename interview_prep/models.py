from django.conf import settings
from django.db import models


class InterviewSession(models.Model):
    INTERVIEW_TYPE_CHOICES = [
        ("technical", "Technical"),
        ("hr", "HR"),
        ("custom", "Custom"),
        ("mixed", "Mixed"),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ("fresher", "Fresher"),
        ("experienced", "Experienced"),
    ]

    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("interrupted", "Interrupted"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="interview_sessions",
    )

    interview_type = models.CharField(
        max_length=20,
        choices=INTERVIEW_TYPE_CHOICES,
        default="technical",
    )

    custom_interview_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )

    target_role = models.CharField(
        max_length=100,
        default="Software Developer",
    )

    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVEL_CHOICES,
        default="fresher",
    )

    experience_duration = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="in_progress",
    )

    total_questions = models.PositiveIntegerField(
        default=30,
    )

    current_question = models.PositiveIntegerField(
        default=1,
    )

    attempted_questions = models.PositiveIntegerField(
        default=0,
    )

    readiness_score = models.FloatField(
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"{self.user} - "
            f"{self.interview_type} - "
            f"{self.target_role}"
        )


class InterviewQuestion(models.Model):
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name="questions",
    )

    question_number = models.PositiveIntegerField()

    category = models.CharField(
        max_length=100,
        blank=True,
        default="General",
    )

    question_text = models.TextField()

    answer = models.TextField(
        blank=True,
        default="",
    )

    score = models.FloatField(
        default=0,
    )

    feedback = models.TextField(
        blank=True,
        default="",
    )

    strengths = models.JSONField(
        default=list,
        blank=True,
    )

    improvements = models.JSONField(
        default=list,
        blank=True,
    )

    is_attempted = models.BooleanField(
        default=False,
    )

    attempted_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["question_number"]

        constraints = [
            models.UniqueConstraint(
                fields=["session", "question_number"],
                name="unique_question_per_session",
            )
        ]

    def __str__(self):
        return (
            f"Session {self.session_id} - "
            f"Question {self.question_number}"
        )