from django.urls import path

from .views import (
    DashboardView,
    ResumeUploadView,
    ResumeListView,
    ResumeManageView,
    ResumeCopilotHistoryView,
    ResumeCopilotView,
    ResumeAnalyzeView,
    ResumeAnalysisDetailView,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("resumes/", ResumeListView.as_view(), name="resume-list"),
    path("resumes/upload/", ResumeUploadView.as_view(), name="resume-upload"),
    path("resumes/<int:resume_id>/", ResumeManageView.as_view(), name="resume-manage"),
    path("resumes/<int:resume_id>/analyze/", ResumeAnalyzeView.as_view(), name="resume-analyze"),
    path("resumes/<int:resume_id>/analysis/", ResumeAnalysisDetailView.as_view(), name="resume-analysis-detail"),
    path("resumes/<int:resume_id>/copilot/history/", ResumeCopilotHistoryView.as_view(), name="resume-copilot-history"),
    path("resumes/<int:resume_id>/copilot/", ResumeCopilotView.as_view(), name="resume-copilot"),
]
