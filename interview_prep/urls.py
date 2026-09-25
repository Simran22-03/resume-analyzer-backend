from django.urls import path

from .views import (
    StartInterviewView,
    InterviewSessionListView,
    InterviewSessionDetailView,
    InterviewQuestionListView,
    SubmitInterviewAnswerView,
    CompleteInterviewView,
    InterviewResultView,
    QuickPracticeView,
    QuickPracticeAnswerView,
)


urlpatterns = [

    # ========================================================
    # FULL INTERVIEW
    # ========================================================

    # Create / Start Interview
    path("create/",StartInterviewView.as_view(),name="start-interview",),

    # List all user's interview sessions
    path("sessions/",InterviewSessionListView.as_view(),name="interview-session-list",),

    # Get single interview session with questions
    path("session/<int:session_id>/",InterviewSessionDetailView.as_view(),name="interview-session-detail",),

    # Get questions for a specific interview
    path("session/<int:session_id>/questions/",InterviewQuestionListView.as_view(),name="interview-question-list",),

    # Submit answer for a question
    path("session/<int:session_id>/answer/",SubmitInterviewAnswerView.as_view(),name="submit-interview-answer",),

    # Complete interview manually
    path("session/<int:session_id>/complete/",CompleteInterviewView.as_view(),name="complete-interview",),

    # Get final interview result
    path("session/<int:session_id>/result/",InterviewResultView.as_view(),name="interview-result",),

    # ========================================================
    # QUICK PRACTICE
    # ========================================================

    # Generate Quick Practice questions
    path("quick-practice/",QuickPracticeView.as_view(),name="quick-practice",),

    # Evaluate Quick Practice answer
    path("quick-practice/evaluate/",QuickPracticeAnswerView.as_view(),name="quick-practice-evaluate",),
]
