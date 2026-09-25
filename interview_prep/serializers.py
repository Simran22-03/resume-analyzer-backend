from rest_framework import serializers

from .models import (
    InterviewSession,
    InterviewQuestion,
)


# ============================================================
# INTERVIEW QUESTION SERIALIZER
# ============================================================

class InterviewQuestionSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = InterviewQuestion

        fields = [
            "id",
            "question_number",
            "category",
            "question_text",
            "answer",
            "score",
            "feedback",
            "strengths",
            "improvements",
            "is_attempted",
            "attempted_at",
        ]

        read_only_fields = [
            "id",
            "question_number",
            "score",
            "feedback",
            "strengths",
            "improvements",
            "is_attempted",
            "attempted_at",
        ]


# ============================================================
# INTERVIEW SESSION SERIALIZER
# ============================================================

class InterviewSessionSerializer(
    serializers.ModelSerializer
):

    questions = InterviewQuestionSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = InterviewSession

        fields = [
            "id",
            "interview_type",
            "custom_interview_type",
            "target_role",
            "experience_level",
            "experience_duration",
            "status",
            "total_questions",
            "current_question",
            "attempted_questions",
            "readiness_score",
            "questions",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "current_question",
            "attempted_questions",
            "readiness_score",
            "questions",
            "created_at",
            "updated_at",
        ]


# ============================================================
# START INTERVIEW
# ============================================================

class StartInterviewSerializer(
    serializers.Serializer
):

    interview_type = serializers.ChoiceField(
        choices=[
            ("technical", "Technical"),
            ("hr", "HR"),
            ("custom", "Custom"),
            ("mixed", "Mixed"),
        ]
    )

    custom_interview_type = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    target_role = serializers.CharField(
        required=False,
        default="Software Developer",
    )

    experience_level = serializers.ChoiceField(
        choices=[
            ("fresher", "Fresher"),
            ("experienced", "Experienced"),
        ],
        required=False,
        default="fresher",
    )

    experience_duration = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    technical_topic = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    total_questions = serializers.IntegerField(
        required=False,
        default=30,
        min_value=1,
        max_value=50,
    )

    def validate(self, attrs):

        interview_type = attrs.get(
            "interview_type"
        )

        custom_type = attrs.get(
            "custom_interview_type"
        )

        if (
            interview_type == "custom"
            and not custom_type
        ):
            raise serializers.ValidationError(
                {
                    "custom_interview_type":
                        "Please specify the custom interview type."
                }
            )

        if (
            attrs.get("experience_level")
            == "experienced"
            and not attrs.get("experience_duration")
        ):
            raise serializers.ValidationError(
                {
                    "experience_duration":
                        "Please provide experience duration."
                }
            )

        return attrs


# ============================================================
# SUBMIT INTERVIEW ANSWER
# ============================================================

class InterviewAnswerSerializer(
    serializers.Serializer
):

    question_id = serializers.IntegerField()

    answer = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )


# ============================================================
# QUICK PRACTICE QUESTION
# ============================================================

class QuickPracticeQuestionSerializer(
    serializers.Serializer
):

    question = serializers.CharField()

    category = serializers.CharField(
        required=False,
        allow_blank=True,
        default="General",
    )


# ============================================================
# QUICK PRACTICE REQUEST
# ============================================================

class QuickPracticeSerializer(
    serializers.Serializer
):

    practice_type = serializers.ChoiceField(
        choices=[
            ("technical", "Technical"),
            ("hr", "HR"),
            ("behavioral", "Behavioral"),
        ]
    )

    target_role = serializers.CharField(
        required=False,
        default="Software Engineer",
    )

    topic = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    difficulty = serializers.ChoiceField(
        choices=[
            ("easy", "Easy"),
            ("medium", "Medium"),
            ("hard", "Hard"),
        ],
        required=False,
        default="medium",
    )

    question_count = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=20,
    )


# ============================================================
# QUICK PRACTICE ANSWER
# ============================================================

class QuickPracticeAnswerSerializer(
    serializers.Serializer
):

    question = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )

    answer = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )

    category = serializers.CharField(
        required=False,
        allow_blank=True,
        default="General",
    )

    practice_type = serializers.CharField(
        required=False,
        allow_blank=True,
        default="technical",
    )