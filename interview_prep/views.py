from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import (
    InterviewSession,
    InterviewQuestion,
)

from .serializers import (
    InterviewSessionSerializer,
    InterviewQuestionSerializer,
    StartInterviewSerializer,
    InterviewAnswerSerializer,
    QuickPracticeSerializer,
    QuickPracticeQuestionSerializer,
)

from .services import (
    generate_interview_questions,
    evaluate_interview_answer,
    generate_quick_practice_questions,
    evaluate_quick_practice_answer,
)


# ============================================================
# CREATE / START FULL INTERVIEW
# ============================================================

class StartInterviewView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        serializer = StartInterviewSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": "Invalid interview details.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        interview_type = data.get(
            "interview_type"
        )

        custom_interview_type = data.get(
            "custom_interview_type",
            "",
        )

        target_role = data.get(
            "target_role",
            "Software Developer",
        )

        experience_level = data.get(
            "experience_level",
            "fresher",
        )

        experience_duration = data.get(
            "experience_duration",
            "",
        )

        technical_topic = data.get(
            "technical_topic",
            "",
        )

        total_questions = data.get(
            "total_questions",
            30,
        )

        try:

            # ------------------------------------------------
            # Generate questions using Groq
            # ------------------------------------------------

            generated_questions = (
                generate_interview_questions(
                    interview_type=interview_type,
                    target_role=target_role,
                    experience_level=experience_level,
                    experience_duration=experience_duration,
                    custom_interview_type=custom_interview_type,
                    technical_topic=technical_topic,
                    total_questions=total_questions,
                )
            )

            # ------------------------------------------------
            # Save session and questions
            # ------------------------------------------------

            with transaction.atomic():

                session = InterviewSession.objects.create(
                    user=request.user,
                    interview_type=interview_type,
                    custom_interview_type=(
                        custom_interview_type or ""
                    ),
                    target_role=target_role,
                    experience_level=experience_level,
                    experience_duration=(
                        experience_duration or ""
                    ),
                    status="in_progress",
                    total_questions=total_questions,
                    current_question=1,
                    attempted_questions=0,
                    readiness_score=0,
                )

                for index, item in enumerate(
                    generated_questions,
                    start=1,
                ):

                    InterviewQuestion.objects.create(
                        session=session,
                        question_number=index,
                        category=item.get(
                            "category",
                            "General",
                        ),
                        question_text=item.get(
                            "question",
                            "",
                        ),
                    )

            # ------------------------------------------------
            # Return complete session
            # ------------------------------------------------

            session_serializer = (
                InterviewSessionSerializer(
                    session
                )
            )

            return Response(
                {
                    "success": True,
                    "message": (
                        "Interview created successfully."
                    ),
                    "session": session_serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Unable to generate "
                        "interview questions."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================
# LIST INTERVIEW SESSIONS
# ============================================================

class InterviewSessionListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        sessions = (
            InterviewSession.objects
            .filter(
                user=request.user
            )
            .prefetch_related(
                "questions"
            )
            .order_by(
                "-created_at"
            )
        )

        serializer = InterviewSessionSerializer(
            sessions,
            many=True,
        )

        return Response(
            {
                "success": True,
                "sessions": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# GET SINGLE INTERVIEW SESSION
# ============================================================

class InterviewSessionDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
        session_id,
    ):

        session = get_object_or_404(
            InterviewSession,
            id=session_id,
            user=request.user,
        )

        serializer = InterviewSessionSerializer(
            session
        )

        return Response(
            {
                "success": True,
                "session": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# GET QUESTIONS
# ============================================================

class InterviewQuestionListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
        session_id,
    ):

        session = get_object_or_404(
            InterviewSession,
            id=session_id,
            user=request.user,
        )

        questions = (
            InterviewQuestion.objects
            .filter(
                session=session
            )
            .order_by(
                "question_number"
            )
        )

        serializer = InterviewQuestionSerializer(
            questions,
            many=True,
        )

        return Response(
            {
                "success": True,
                "questions": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# SUBMIT INTERVIEW ANSWER
# ============================================================

class SubmitInterviewAnswerView(APIView):

    permission_classes = [IsAuthenticated]

    def post(
        self,
        request,
        session_id,
    ):

        serializer = InterviewAnswerSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": "Invalid answer.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        question_id = serializer.validated_data.get(
            "question_id"
        )

        answer = serializer.validated_data.get(
            "answer"
        )

        question = get_object_or_404(
            InterviewQuestion,
            id=question_id,
            session__id=session_id,
            session__user=request.user,
        )

        session = question.session

        # ----------------------------------------------------
        # Prevent answering an already completed interview
        # ----------------------------------------------------

        if session.status == "completed":

            return Response(
                {
                    "success": False,
                    "message": "This interview has already been completed.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            # ------------------------------------------------
            # Evaluate answer using Groq
            # ------------------------------------------------

            evaluation = (
                evaluate_interview_answer(
                    question=question.question_text,
                    answer=answer,
                    category=question.category,
                    interview_type=session.interview_type,
                    target_role=session.target_role,
                    experience_level=session.experience_level,
                )
            )

            score = evaluation.get(
                "score",
                0,
            )

            feedback = evaluation.get(
                "feedback",
                "",
            )

            strengths = evaluation.get(
                "strengths",
                [],
            )

            improvements = evaluation.get(
                "improvements",
                [],
            )

            # ------------------------------------------------
            # Save answer and evaluation
            # ------------------------------------------------

            question.answer = answer
            question.score = score
            question.feedback = feedback
            question.strengths = strengths
            question.improvements = improvements
            question.is_attempted = True
            question.attempted_at = timezone.now()

            question.save()

            # ------------------------------------------------
            # Calculate progress
            # ------------------------------------------------

            attempted_questions = (
                InterviewQuestion.objects
                .filter(
                    session=session,
                    is_attempted=True,
                )
            )

            attempted_count = (
                attempted_questions.count()
            )

            scores = list(
                attempted_questions.values_list(
                    "score",
                    flat=True,
                )
            )

            valid_scores = [
                float(score)
                for score in scores
                if score is not None
            ]

            if valid_scores:

                readiness_score = (
                    sum(valid_scores)
                    / len(valid_scores)
                )

            else:

                readiness_score = 0

            session.attempted_questions = (
                attempted_count
            )

            session.readiness_score = round(
                readiness_score,
                2,
            )

            # ------------------------------------------------
            # Determine next question
            # ------------------------------------------------

            next_question = (
                InterviewQuestion.objects
                .filter(
                    session=session,
                    is_attempted=False,
                )
                .order_by(
                    "question_number"
                )
                .first()
            )

            if next_question:

                session.current_question = (
                    next_question.question_number
                )

            else:

                session.status = "completed"

                session.current_question = (
                    session.total_questions
                )

            session.save()

            # ------------------------------------------------
            # Return evaluation
            # ------------------------------------------------

            return Response(
                {
                    "success": True,
                    "message": (
                        "Answer evaluated successfully."
                    ),
                    "evaluation": evaluation,
                    "question": (
                        InterviewQuestionSerializer(
                            question
                        ).data
                    ),
                    "session": {
                        "id": session.id,
                        "attempted_questions": (
                            session.attempted_questions
                        ),
                        "total_questions": (
                            session.total_questions
                        ),
                        "current_question": (
                            session.current_question
                        ),
                        "readiness_score": (
                            session.readiness_score
                        ),
                        "status": session.status,
                    },
                    "completed": (
                        session.status == "completed"
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Unable to evaluate "
                        "interview answer."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

class InterviewAnswerView(
    SubmitInterviewAnswerView
):
    pass


# ============================================================
# COMPLETE INTERVIEW
# ============================================================

class CompleteInterviewView(APIView):

    permission_classes = [IsAuthenticated]

    def post(
        self,
        request,
        session_id,
    ):

        session = get_object_or_404(
            InterviewSession,
            id=session_id,
            user=request.user,
        )

        attempted_questions = (
            InterviewQuestion.objects
            .filter(
                session=session,
                is_attempted=True,
            )
        )

        scores = list(
            attempted_questions.values_list(
                "score",
                flat=True,
            )
        )

        valid_scores = [
            float(score)
            for score in scores
            if score is not None
        ]

        if valid_scores:

            readiness_score = (
                sum(valid_scores)
                / len(valid_scores)
            )

        else:

            readiness_score = 0

        session.status = "completed"

        session.attempted_questions = (
            attempted_questions.count()
        )

        session.readiness_score = round(
            readiness_score,
            2,
        )

        if session.attempted_questions > 0:

            session.current_question = min(
                session.total_questions,
                session.attempted_questions,
            )

        session.save()

        serializer = InterviewSessionSerializer(
            session
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Interview completed successfully."
                ),
                "session": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# INTERVIEW RESULT
# ============================================================

class InterviewResultView(APIView):

    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
        session_id,
    ):

        session = get_object_or_404(
            InterviewSession,
            id=session_id,
            user=request.user,
        )

        questions = (
            InterviewQuestion.objects
            .filter(
                session=session
            )
            .order_by(
                "question_number"
            )
        )

        attempted_questions = questions.filter(
            is_attempted=True
        )

        scores = list(
            attempted_questions.values_list(
                "score",
                flat=True,
            )
        )

        valid_scores = [
            float(score)
            for score in scores
            if score is not None
        ]

        # ----------------------------------------------------
        # OVERALL SCORE
        # ----------------------------------------------------

        if valid_scores:

            overall_score = (
                sum(valid_scores)
                / len(valid_scores)
            )

        else:

            overall_score = 0

        overall_score = round(
            overall_score,
            2,
        )

        # ----------------------------------------------------
        # STRENGTHS
        # ----------------------------------------------------

        strengths = []

        for question in attempted_questions:

            if isinstance(
                question.strengths,
                list,
            ):

                strengths.extend(
                    question.strengths
                )

        strengths = list(
            dict.fromkeys(
                str(item).strip()
                for item in strengths
                if str(item).strip()
            )
        )

        # ----------------------------------------------------
        # IMPROVEMENTS
        # ----------------------------------------------------

        improvements = []

        for question in attempted_questions:

            if isinstance(
                question.improvements,
                list,
            ):

                improvements.extend(
                    question.improvements
                )

        improvements = list(
            dict.fromkeys(
                str(item).strip()
                for item in improvements
                if str(item).strip()
            )
        )

        # ----------------------------------------------------
        # UPDATE SESSION
        # ----------------------------------------------------

        session.attempted_questions = (
            attempted_questions.count()
        )

        session.readiness_score = (
            overall_score
        )

        if (
            session.attempted_questions
            >= session.total_questions
        ):

            session.status = "completed"

            session.current_question = (
                session.total_questions
            )

        session.save()

        # ----------------------------------------------------
        # QUESTION RESULTS
        # ----------------------------------------------------

        question_results = []

        for question in questions:

            question_results.append(
                {
                    "id": question.id,

                    "question_number": (
                        question.question_number
                    ),

                    "category": (
                        question.category
                    ),

                    "question_text": (
                        question.question_text
                    ),

                    "answer": (
                        question.answer
                        or ""
                    ),

                    "score": (
                        question.score
                        if question.is_attempted
                        else None
                    ),

                    "feedback": (
                        question.feedback
                        if question.is_attempted
                        else ""
                    ),

                    "strengths": (
                        question.strengths
                        if question.is_attempted
                        else []
                    ),

                    "improvements": (
                        question.improvements
                        if question.is_attempted
                        else []
                    ),

                    "is_attempted": (
                        question.is_attempted
                    ),

                    "attempted_at": (
                        question.attempted_at
                    ),
                }
            )

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        return Response(
            {
                "success": True,

                "result": {
                    "session_id": session.id,

                    "interview_type": (
                        session.interview_type
                    ),

                    "custom_interview_type": (
                        session.custom_interview_type
                    ),

                    "target_role": (
                        session.target_role
                    ),

                    "experience_level": (
                        session.experience_level
                    ),

                    "experience_duration": (
                        session.experience_duration
                    ),

                    "status": (
                        session.status
                    ),

                    "total_questions": (
                        session.total_questions
                    ),

                    "attempted_questions": (
                        session.attempted_questions
                    ),

                    "overall_score": (
                        overall_score
                    ),

                    "readiness_score": (
                        session.readiness_score
                    ),

                    "strengths": strengths,

                    "improvements": improvements,

                    "questions": question_results,

                    "created_at": (
                        session.created_at
                    ),

                    "updated_at": (
                        session.updated_at
                    ),
                }
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# QUICK PRACTICE
# ============================================================

class QuickPracticeView(APIView):

    permission_classes = [IsAuthenticated]

    def post(
        self,
        request,
    ):

        serializer = QuickPracticeSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                {
                    "success": False,
                    "message": (
                        "Invalid Quick Practice details."
                    ),
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        practice_type = data.get(
            "practice_type"
        )

        topic = data.get(
            "topic",
            "",
        )

        difficulty = data.get(
            "difficulty",
            "medium",
        )

        question_count = data.get(
            "question_count",
            5,
        )

        target_role = request.data.get(
            "target_role",
            "Software Engineer",
        )

        try:

            questions = (
                generate_quick_practice_questions(
                    practice_type=practice_type,
                    target_role=target_role,
                    topic=topic or "",
                    difficulty=difficulty,
                    question_count=question_count,
                )
            )

            output_serializer = (
                QuickPracticeQuestionSerializer(
                    data=questions,
                    many=True,
                )
            )

            output_serializer.is_valid(
                raise_exception=True
            )

            return Response(
                {
                    "success": True,
                    "message": (
                        "Quick Practice questions "
                        "generated successfully."
                    ),
                    "questions": (
                        output_serializer.data
                    ),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Unable to generate "
                        "Quick Practice questions."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ============================================================
# QUICK PRACTICE ANSWER
# ============================================================

class QuickPracticeAnswerView(APIView):

    permission_classes = [IsAuthenticated]

    def post(
        self,
        request,
    ):

        question = request.data.get(
            "question"
        )

        answer = request.data.get(
            "answer"
        )

        category = request.data.get(
            "category",
            "General",
        )

        practice_type = request.data.get(
            "practice_type",
            "technical",
        )

        if not question:

            return Response(
                {
                    "success": False,
                    "message": "Question is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not answer:

            return Response(
                {
                    "success": False,
                    "message": "Answer is required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            evaluation = (
                evaluate_quick_practice_answer(
                    question=question,
                    answer=answer,
                    category=category,
                    practice_type=practice_type,
                )
            )

            return Response(
                {
                    "success": True,
                    "message": (
                        "Quick Practice answer "
                        "evaluated successfully."
                    ),
                    "evaluation": evaluation,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as exc:

            return Response(
                {
                    "success": False,
                    "message": (
                        "Unable to evaluate "
                        "Quick Practice answer."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )