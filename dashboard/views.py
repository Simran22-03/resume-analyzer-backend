from django.core.files.storage import default_storage

from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Resume, ResumeAnalysis, ChatHistory
from .serializers import ResumeSerializer
from .groq_service import analyze_resume
from .copilot_service import chat_with_specific_resume
from .services import extract_text_from_pdf


# =========================================================
# EMPLOYEE DASHBOARD
# =========================================================

class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        resumes = Resume.objects.filter(
            user=user
        )

        latest_resume = resumes.order_by(
            "-uploaded_at"
        ).first()

        if latest_resume:
            resume_data = {
                "uploaded": True,
                "status": "Resume uploaded",
            }
        else:
            resume_data = {
                "uploaded": False,
                "status": "No resume uploaded yet",
            }

        return Response(
            {
                "user": {
                    "id": user.id,
                    "name": user.first_name,
                    "email": user.email,
                    "role": user.role,
                    "company_name": user.company_name,
                },

                "statistics": {
                    "resumes_analyzed": resumes.filter(
                        is_analyzed=True
                    ).count(),

                    "comparisons": 0,

                    "interviews": 0,
                },

                "recent_activity": [],

                "resume": resume_data,
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# UPLOAD RESUME
# =========================================================

class ResumeUploadView(APIView):
    permission_classes = [IsAuthenticated]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def post(self, request):
        serializer = ResumeSerializer(
            data=request.data
        )

        if serializer.is_valid():
            resume = serializer.save(
                user=request.user
            )

            return Response(
                {
                    "message": "Resume uploaded successfully.",

                    "resume": ResumeSerializer(
                        resume
                    ).data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


# =========================================================
# LIST USER'S RESUMES
# =========================================================

class ResumeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        resumes = Resume.objects.filter(
            user=request.user
        ).order_by(
            "-uploaded_at"
        )

        serializer = ResumeSerializer(
            resumes,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# =========================================================
# RENAME / DELETE RESUME
# =========================================================

class ResumeManageView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, resume_id):
        new_name = str(
            request.data.get("name", "")
        ).strip()

        if not new_name:
            return Response(
                {
                    "message": "Resume name is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # A resume name must be a filename, not a path.
        if "/" in new_name or "\\" in new_name:
            return Response(
                {
                    "message": "Invalid resume name."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_name = new_name.rsplit("/", 1)[-1]

        if not new_name.lower().endswith(".pdf"):
            new_name = f"{new_name}.pdf"

        try:
            resume = Resume.objects.get(
                id=resume_id,
                user=request.user,
            )
        except Resume.DoesNotExist:
            return Response(
                {
                    "message": "Resume not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        old_file_name = resume.file.name
        directory = (
            old_file_name.rsplit("/", 1)[0]
            if "/" in old_file_name
            else ""
        )

        new_file_name = (
            f"{directory}/{new_name}"
            if directory
            else new_name
        )

        if (
            new_file_name != old_file_name
            and default_storage.exists(new_file_name)
        ):
            return Response(
                {
                    "message": "A resume with this name already exists."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_file_name != old_file_name:
            try:
                with resume.file.open("rb") as old_file:
                    default_storage.save(
                        new_file_name,
                        old_file,
                    )

                default_storage.delete(
                    old_file_name
                )

                resume.file.name = new_file_name
                resume.save(
                    update_fields=["file"]
                )

            except Exception as exc:
                if default_storage.exists(new_file_name):
                    default_storage.delete(
                        new_file_name
                    )

                return Response(
                    {
                        "message": "Unable to rename the resume.",
                        "error": str(exc),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        return Response(
            {
                "message": "Resume renamed successfully.",
                "resume": ResumeSerializer(
                    resume
                ).data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, resume_id):
        try:
            resume = Resume.objects.get(
                id=resume_id,
                user=request.user,
            )
        except Resume.DoesNotExist:
            return Response(
                {
                    "message": "Resume not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            file_name = resume.file.name

            if file_name:
                default_storage.delete(file_name)

            # ResumeAnalysis is linked with
            # on_delete=models.CASCADE, so its
            # analysis is removed with the resume.
            resume.delete()

        except Exception as exc:
            return Response(
                {
                    "message": "Unable to delete the resume.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "Resume deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT,
        )


# =========================================================
# ANALYZE RESUME
# =========================================================

class ResumeAnalyzeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, resume_id):

        job_description = request.data.get(
            "job_description",
            ""
        ).strip()

        if not job_description:
            return Response(
                {
                    "message": "Job description is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # Find resume belonging to logged-in user
        # -------------------------------------------------

        try:
            resume = Resume.objects.get(
                id=resume_id,
                user=request.user,
            )

        except Resume.DoesNotExist:
            return Response(
                {
                    "message": "Resume not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -------------------------------------------------
        # Extract PDF text
        # -------------------------------------------------

        try:

            with resume.file.open("rb") as pdf_file:

                resume_text = extract_text_from_pdf(
                    pdf_file
                )

        except Exception as exc:

            return Response(
                {
                    "message": "Unable to read the resume PDF.",
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not resume_text or not resume_text.strip():
            return Response(
                {
                    "message": (
                        "No readable text was found in the resume PDF."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # Send resume + JD to Groq
        # -------------------------------------------------

        try:

            analysis_result = analyze_resume(
                resume_text=resume_text,
                job_description=job_description,
            )

        except Exception as exc:

            return Response(
                {
                    "message": "Resume analysis failed.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # -------------------------------------------------
        # Save analysis in database
        # -------------------------------------------------

        try:

            analysis, _ = (
                ResumeAnalysis.objects.update_or_create(
                    resume=resume,

                    defaults={
                        "job_description": job_description,

                        "ats_score": analysis_result[
                            "ats_score"
                        ],

                        "strengths": analysis_result[
                            "strengths"
                        ],

                        "missing_skills": analysis_result[
                            "missing_skills"
                        ],

                        "weaknesses": analysis_result[
                            "weaknesses"
                        ],

                        "suggestions": analysis_result[
                            "suggestions"
                        ],
                    },
                )
            )

        except Exception as exc:

            return Response(
                {
                    "message": (
                        "Analysis was generated but could not be saved."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # -------------------------------------------------
        # Mark resume as analyzed
        # -------------------------------------------------

        resume.is_analyzed = True

        resume.save(
            update_fields=["is_analyzed"]
        )

        # -------------------------------------------------
        # Return analysis
        # -------------------------------------------------

        return Response(
            {
                "message": "Resume analyzed successfully.",

                "analysis": {
                    "id": analysis.id,

                    "resume_id": resume.id,

                    "ats_score": analysis.ats_score,

                    "strengths": analysis.strengths,

                    "missing_skills": (
                        analysis.missing_skills
                    ),

                    "weaknesses": (
                        analysis.weaknesses
                    ),

                    "suggestions": (
                        analysis.suggestions
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# GET SAVED RESUME ANALYSIS
# =========================================================

class ResumeAnalysisDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, resume_id):

        # -------------------------------------------------
        # Make sure resume belongs to logged-in user
        # -------------------------------------------------

        try:
            resume = Resume.objects.get(
                id=resume_id,
                user=request.user,
            )

        except Resume.DoesNotExist:

            return Response(
                {
                    "message": "Resume not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -------------------------------------------------
        # Get saved analysis
        # -------------------------------------------------

        try:

            analysis = ResumeAnalysis.objects.get(
                resume=resume
            )

        except ResumeAnalysis.DoesNotExist:

            return Response(
                {
                    "message": (
                        "Analysis not found for this resume."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -------------------------------------------------
        # Return complete analysis
        # -------------------------------------------------

        return Response(
            {
                "resume": {
                    "id": resume.id,

                    "file": (
                        resume.file.url
                        if resume.file
                        else None
                    ),

                    "uploaded_at": (
                        resume.uploaded_at
                    ),

                    "is_analyzed": (
                        resume.is_analyzed
                    ),
                },

                "analysis": {
                    "id": analysis.id,

                    "resume_id": resume.id,

                    "ats_score": (
                        analysis.ats_score
                    ),

                    "strengths": (
                        analysis.strengths
                    ),

                    "missing_skills": (
                        analysis.missing_skills
                    ),

                    "weaknesses": (
                        analysis.weaknesses
                    ),

                    "suggestions": (
                        analysis.suggestions
                    ),
                },
            },
            status=status.HTTP_200_OK,
        )

# =========================================================
# RESUME-SPECIFIC COPILOT HISTORY
# =========================================================

class ResumeCopilotHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, resume_id):

        try:
            resume = Resume.objects.get(
                id=resume_id,
                user=request.user,
            )

        except Resume.DoesNotExist:

            return Response(
                {
                    "message": "Resume not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        messages = list(
            ChatHistory.objects.filter(
                user=request.user,
                resume=resume,
            )
            .order_by("-created_at")[:10]
        )

        messages.reverse()

        return Response(
            {
                "resume_id": resume.id,

                "messages": [
                    {
                        "id": message.id,
                        "role": message.role,
                        "content": message.message,
                        "created_at": message.created_at,
                    }
                    for message in messages
                ],
            },
            status=status.HTTP_200_OK,
        )


# =========================================================
# RESUME-SPECIFIC COPILOT
# =========================================================

class ResumeCopilotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, resume_id):

        user_message = str(
            request.data.get(
                "message",
                "",
            )
        ).strip()

        if not user_message:

            return Response(
                {
                    "message": "Message is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # SECURITY:
        # The resume MUST belong to the logged-in user.
        # The frontend cannot select another user's resume.
        # -------------------------------------------------

        try:

            resume = Resume.objects.get(
                id=resume_id,
                user=request.user,
            )

        except Resume.DoesNotExist:

            return Response(
                {
                    "message": "Resume not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -------------------------------------------------
        # Get the analysis that belongs to this resume.
        # -------------------------------------------------

        try:

            analysis = ResumeAnalysis.objects.get(
                resume=resume
            )

        except ResumeAnalysis.DoesNotExist:

            return Response(
                {
                    "message": (
                        "Analysis not found for this resume."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -------------------------------------------------
        # HISTORY COMES FROM DATABASE ONLY.
        #
        # The frontend does NOT send history anymore.
        # -------------------------------------------------

        stored_messages = list(
            ChatHistory.objects.filter(
                user=request.user,
                resume=resume,
            )
            .order_by("-created_at")[:10]
        )

        stored_messages.reverse()

        history = [
            {
                "role": item.role,
                "content": item.message,
            }
            for item in stored_messages
        ]

        # -------------------------------------------------
        # Extract ONLY this resume's PDF.
        # -------------------------------------------------

        try:

            with resume.file.open(
                "rb"
            ) as pdf_file:

                resume_text = (
                    extract_text_from_pdf(
                        pdf_file
                    )
                )

        except Exception as exc:

            return Response(
                {
                    "message": (
                        "Unable to read the resume PDF."
                    ),
                    "error": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not resume_text or not resume_text.strip():

            return Response(
                {
                    "message": (
                        "No readable text was found in the resume PDF."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -------------------------------------------------
        # Ask Groq using backend-owned history.
        # -------------------------------------------------

        try:

            reply = chat_with_specific_resume(
                resume_text=resume_text,

                job_description=(
                    analysis.job_description
                ),

                ats_score=analysis.ats_score,

                strengths=analysis.strengths,

                missing_skills=(
                    analysis.missing_skills
                ),

                weaknesses=analysis.weaknesses,

                suggestions=analysis.suggestions,

                history=history,

                user_message=user_message,
            )

        except Exception as exc:

            print(
                "\n========== COPILOT VIEW ERROR =========="
            )

            print(
                f"{type(exc).__name__}: {exc}"
            )

            print(
                "========================================\n"
            )

            return Response(
                {
                    "message": "Copilot response failed.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # -------------------------------------------------
        # Save BOTH sides of the conversation.
        # -------------------------------------------------

        ChatHistory.objects.create(
            user=request.user,
            resume=resume,
            role="user",
            message=user_message,
        )

        ChatHistory.objects.create(
            user=request.user,
            resume=resume,
            role="assistant",
            message=reply,
        )

        # -------------------------------------------------
        # Keep ONLY the latest 10 messages for THIS
        # user + THIS resume.
        # -------------------------------------------------

        old_ids = list(
            ChatHistory.objects.filter(
                user=request.user,
                resume=resume,
            )
            .order_by("-created_at")
            .values_list(
                "id",
                flat=True,
            )[10:]
        )

        if old_ids:

            ChatHistory.objects.filter(
                id__in=old_ids
            ).delete()

        # -------------------------------------------------
        # Return backend-owned latest history.
        # Frontend uses this only for display.
        # -------------------------------------------------

        latest_messages = list(
            ChatHistory.objects.filter(
                user=request.user,
                resume=resume,
            )
            .order_by("-created_at")[:10]
        )

        latest_messages.reverse()

        return Response(
            {
                "reply": reply,

                "resume_id": resume.id,

                "resume_name": resume.file.name,

                "messages": [
                    {
                        "id": item.id,
                        "role": item.role,
                        "content": item.message,
                        "created_at": item.created_at,
                    }
                    for item in latest_messages
                ],
            },
            status=status.HTTP_200_OK,
        )
