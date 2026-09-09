from io import BytesIO

from django.http import FileResponse

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ResumeBuilder
from .serializers import ResumeBuilderSerializer
from .groq_service import generate_professional_summary


class ResumeBuilderViewSet(viewsets.ModelViewSet):

    serializer_class = ResumeBuilderSerializer
    permission_classes = [IsAuthenticated]

    # =========================================================
    # QUERYSET
    # =========================================================

    def get_queryset(self):

        return (
            ResumeBuilder.objects
            .filter(user=self.request.user)
            .prefetch_related(
                "experiences",
                "education",
                "skills",
                "projects",
            )
            .order_by("-updated_at")
        )

    # =========================================================
    # CREATE
    # =========================================================

    def perform_create(self, serializer):

        serializer.save(
            user=self.request.user
        )

    # =========================================================
    # DELETE
    # =========================================================

    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):

        resume = self.get_object()

        resume.delete()

        return Response(
            {
                "message": "Resume deleted successfully."
            },
            status=status.HTTP_200_OK,
        )

    # =========================================================
    # GENERATE RESUME
    # =========================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="generate",
    )
    def generate(
        self,
        request,
        pk=None,
    ):

        resume = self.get_object()

        resume.is_generated = True

        resume.save(
            update_fields=[
                "is_generated",
                "updated_at",
            ]
        )

        serializer = self.get_serializer(
            resume
        )

        return Response(
            {
                "message": "Resume generated successfully.",
                "resume": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    # =========================================================
    # AI PROFESSIONAL SUMMARY
    #
    # IMPORTANT:
    #
    # detail=False
    #
    # Because the resume does NOT exist yet when the user
    # generates the professional summary.
    #
    # Endpoint:
    #
    # POST /api/resume-builder/resumes/generate-summary/
    #
    # =========================================================

    @action(
        detail=False,
        methods=["post"],
        url_path="generate-summary",
    )
    def generate_summary(
        self,
        request,
    ):

        job_description = str(
            request.data.get(
                "job_description",
                "",
            )
        ).strip()

        # -----------------------------------------------------
        # Validate job description
        # -----------------------------------------------------

        if not job_description:

            return Response(
                {
                    "message": (
                        "Job description, career goal, "
                        "or target role is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------------------------------
        # Resume information coming from frontend
        # -----------------------------------------------------

        name = str(
            request.data.get(
                "full_name",
                "",
            )
        ).strip()

        professional_title = str(
            request.data.get(
                "professional_title",
                "",
            )
        ).strip()

        experiences = request.data.get(
            "experiences",
            [],
        )

        education = request.data.get(
            "education",
            [],
        )

        skills = request.data.get(
            "skills",
            [],
        )

        projects = request.data.get(
            "projects",
            [],
        )

        # -----------------------------------------------------
        # Convert skills into text
        # -----------------------------------------------------

        if isinstance(skills, list):

            skill_names = []

            for skill in skills:

                if isinstance(skill, dict):

                    skill_name = str(
                        skill.get(
                            "name",
                            "",
                        )
                    ).strip()

                    if skill_name:
                        skill_names.append(
                            skill_name
                        )

                else:

                    skill_name = str(
                        skill
                    ).strip()

                    if skill_name:
                        skill_names.append(
                            skill_name
                        )

            skills_text = ", ".join(
                skill_names
            )

        else:

            skills_text = str(
                skills
            ).strip()

        # -----------------------------------------------------
        # Convert experience into text
        # -----------------------------------------------------

        experience_lines = []

        if isinstance(
            experiences,
            list,
        ):

            for experience in experiences:

                if not isinstance(
                    experience,
                    dict,
                ):
                    continue

                job_title = str(
                    experience.get(
                        "job_title",
                        "",
                    )
                ).strip()

                company_name = str(
                    experience.get(
                        "company_name",
                        "",
                    )
                ).strip()

                responsibilities = str(
                    experience.get(
                        "responsibilities",
                        "",
                    )
                ).strip()

                start_date = str(
                    experience.get(
                        "start_date",
                        "",
                    )
                ).strip()

                end_date = str(
                    experience.get(
                        "end_date",
                        "",
                    )
                ).strip()

                if (
                    job_title
                    or company_name
                    or responsibilities
                ):

                    experience_lines.append(
                        (
                            f"{job_title} at "
                            f"{company_name} "
                            f"({start_date} - {end_date}): "
                            f"{responsibilities}"
                        )
                    )

        experience_text = "\n".join(
            experience_lines
        )

        # -----------------------------------------------------
        # Convert education into text
        # -----------------------------------------------------

        education_lines = []

        if isinstance(
            education,
            list,
        ):

            for item in education:

                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                degree = str(
                    item.get(
                        "degree",
                        "",
                    )
                ).strip()

                institution = str(
                    item.get(
                        "institution",
                        "",
                    )
                ).strip()

                start_date = str(
                    item.get(
                        "start_date",
                        "",
                    )
                ).strip()

                end_date = str(
                    item.get(
                        "end_date",
                        "",
                    )
                ).strip()

                description = str(
                    item.get(
                        "description",
                        "",
                    )
                ).strip()

                if (
                    degree
                    or institution
                    or description
                ):

                    education_lines.append(
                        (
                            f"{degree} at "
                            f"{institution} "
                            f"({start_date} - {end_date}). "
                            f"{description}"
                        )
                    )

        education_text = "\n".join(
            education_lines
        )

        # -----------------------------------------------------
        # Convert projects into text
        # -----------------------------------------------------

        project_lines = []

        if isinstance(
            projects,
            list,
        ):

            for project in projects:

                if not isinstance(
                    project,
                    dict,
                ):
                    continue

                project_name = str(
                    project.get(
                        "name",
                        "",
                    )
                ).strip()

                description = str(
                    project.get(
                        "description",
                        "",
                    )
                ).strip()

                technologies = str(
                    project.get(
                        "technologies",
                        "",
                    )
                ).strip()

                if (
                    project_name
                    or description
                    or technologies
                ):

                    project_lines.append(
                        (
                            f"{project_name}: "
                            f"{description} "
                            f"Technologies: "
                            f"{technologies}"
                        )
                    )

        project_text = "\n".join(
            project_lines
        )

        # -----------------------------------------------------
        # CALL GROQ
        # -----------------------------------------------------

        try:

            summary = (
                generate_professional_summary(
                    job_description=job_description,
                    name=name,
                    professional_title=professional_title,
                    skills=skills_text,
                    experience=experience_text,
                    education=education_text,
                    projects=project_text,
                )
            )

        except Exception as error:

            print(
                "\n========== AI SUMMARY ERROR =========="
            )

            print(
                f"{type(error).__name__}: {error}"
            )

            print(
                "======================================\n"
            )

            return Response(
                {
                    "message": (
                        "Unable to generate "
                        "professional summary."
                    ),
                    "error": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # -----------------------------------------------------
        # RETURN SUMMARY
        #
        # We DON'T save it here because the resume has not
        # been created yet.
        # -----------------------------------------------------

        return Response(
            {
                "message": (
                    "Professional summary "
                    "generated successfully."
                ),
                "summary": summary,
            },
            status=status.HTTP_200_OK,
        )

    # =========================================================
    # DOWNLOAD
    # =========================================================

    @action(
        detail=True,
        methods=["get"],
        url_path="download",
    )
    def download(
        self,
        request,
        pk=None,
    ):

        resume = self.get_object()

        buffer = BytesIO()

        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        story = []

        # -----------------------------------------------------
        # NAME
        # -----------------------------------------------------

        if resume.full_name:

            story.append(
                Paragraph(
                    resume.full_name,
                    styles["Title"],
                )
            )

        # -----------------------------------------------------
        # PROFESSIONAL TITLE
        # -----------------------------------------------------

        if resume.professional_title:

            story.append(
                Paragraph(
                    resume.professional_title,
                    styles["Heading2"],
                )
            )

        # -----------------------------------------------------
        # CONTACT
        # -----------------------------------------------------

        contact = []

        if resume.email:
            contact.append(
                resume.email
            )

        if resume.phone:
            contact.append(
                resume.phone
            )

        if resume.location:
            contact.append(
                resume.location
            )

        if contact:

            story.append(
                Paragraph(
                    " | ".join(contact),
                    styles["Normal"],
                )
            )

        story.append(
            Spacer(1, 15)
        )

        # -----------------------------------------------------
        # SUMMARY
        # -----------------------------------------------------

        if resume.professional_summary:

            story.append(
                Paragraph(
                    "Professional Summary",
                    styles["Heading2"],
                )
            )

            story.append(
                Paragraph(
                    resume.professional_summary,
                    styles["Normal"],
                )
            )

            story.append(
                Spacer(1, 10)
            )

        # -----------------------------------------------------
        # EXPERIENCE
        # -----------------------------------------------------

        experiences = (
            resume.experiences.all()
        )

        if experiences.exists():

            story.append(
                Paragraph(
                    "Work Experience",
                    styles["Heading2"],
                )
            )

            for experience in experiences:

                story.append(
                    Paragraph(
                        f"<b>{experience.job_title}</b> - "
                        f"{experience.company_name}",
                        styles["Normal"],
                    )
                )

                if experience.location:

                    story.append(
                        Paragraph(
                            experience.location,
                            styles["Normal"],
                        )
                    )

                if (
                    experience.start_date
                    or experience.end_date
                ):

                    dates = (
                        f"{experience.start_date} - "
                        f"{experience.end_date}"
                    )

                    if experience.currently_working:

                        dates = (
                            f"{experience.start_date} "
                            f"- Present"
                        )

                    story.append(
                        Paragraph(
                            dates,
                            styles["Normal"],
                        )
                    )

                if experience.responsibilities:

                    story.append(
                        Paragraph(
                            experience.responsibilities,
                            styles["Normal"],
                        )
                    )

                story.append(
                    Spacer(1, 8)
                )

        # -----------------------------------------------------
        # EDUCATION
        # -----------------------------------------------------

        education = (
            resume.education.all()
        )

        if education.exists():

            story.append(
                Paragraph(
                    "Education",
                    styles["Heading2"],
                )
            )

            for item in education:

                story.append(
                    Paragraph(
                        f"<b>{item.degree}</b> - "
                        f"{item.institution}",
                        styles["Normal"],
                    )
                )

                if item.location:

                    story.append(
                        Paragraph(
                            item.location,
                            styles["Normal"],
                        )
                    )

                if (
                    item.start_date
                    or item.end_date
                ):

                    story.append(
                        Paragraph(
                            f"{item.start_date} - "
                            f"{item.end_date}",
                            styles["Normal"],
                        )
                    )

                if item.description:

                    story.append(
                        Paragraph(
                            item.description,
                            styles["Normal"],
                        )
                    )

                story.append(
                    Spacer(1, 8)
                )

        # -----------------------------------------------------
        # SKILLS
        # -----------------------------------------------------

        skills = resume.skills.all()

        if skills.exists():

            story.append(
                Paragraph(
                    "Skills",
                    styles["Heading2"],
                )
            )

            skill_names = [
                skill.name
                for skill in skills
            ]

            story.append(
                Paragraph(
                    ", ".join(skill_names),
                    styles["Normal"],
                )
            )

            story.append(
                Spacer(1, 10)
            )

        # -----------------------------------------------------
        # PROJECTS
        # -----------------------------------------------------

        projects = resume.projects.all()

        if projects.exists():

            story.append(
                Paragraph(
                    "Projects",
                    styles["Heading2"],
                )
            )

            for project in projects:

                story.append(
                    Paragraph(
                        f"<b>{project.name}</b>",
                        styles["Normal"],
                    )
                )

                if project.description:

                    story.append(
                        Paragraph(
                            project.description,
                            styles["Normal"],
                        )
                    )

                if project.technologies:

                    story.append(
                        Paragraph(
                            f"Technologies: "
                            f"{project.technologies}",
                            styles["Normal"],
                        )
                    )

                if project.project_url:

                    story.append(
                        Paragraph(
                            project.project_url,
                            styles["Normal"],
                        )
                    )

                story.append(
                    Spacer(1, 8)
                )

        # -----------------------------------------------------
        # BUILD PDF
        # -----------------------------------------------------

        document.build(story)

        buffer.seek(0)

        filename = (
            resume.title.replace(
                " ",
                "_",
            )
            if resume.title
            else f"resume_{resume.id}"
        )

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"{filename}.pdf",
            content_type="application/pdf",
        )