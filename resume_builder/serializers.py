from rest_framework import serializers

from .models import (
    ResumeBuilder,
    WorkExperience,
    Education,
    Skill,
    Project,
)


class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = [
            "id",
            "job_title",
            "company_name",
            "location",
            "start_date",
            "end_date",
            "currently_working",
            "responsibilities",
        ]
        read_only_fields = ["id"]


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            "id",
            "degree",
            "institution",
            "location",
            "start_date",
            "end_date",
            "description",
        ]
        read_only_fields = ["id"]


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = [
            "id",
            "name",
        ]
        read_only_fields = ["id"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "technologies",
            "project_url",
        ]
        read_only_fields = ["id"]


class ResumeBuilderSerializer(serializers.ModelSerializer):

    experiences = WorkExperienceSerializer(
        many=True,
        required=False
    )

    education = EducationSerializer(
        many=True,
        required=False
    )

    skills = SkillSerializer(
        many=True,
        required=False
    )

    projects = ProjectSerializer(
        many=True,
        required=False
    )

    class Meta:
        model = ResumeBuilder

        fields = [
            "id",
            "title",
            "full_name",
            "professional_title",
            "email",
            "phone",
            "location",
            "professional_summary",
            "created_at",
            "updated_at",
            "is_generated",
            "experiences",
            "education",
            "skills",
            "projects",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "is_generated",
        ]

    def create(self, validated_data):

        experiences_data = validated_data.pop(
            "experiences",
            []
        )

        education_data = validated_data.pop(
            "education",
            []
        )

        skills_data = validated_data.pop(
            "skills",
            []
        )

        projects_data = validated_data.pop(
            "projects",
            []
        )

        # user is passed from ViewSet.perform_create()
        user = validated_data.pop("user")

        resume = ResumeBuilder.objects.create(
            user=user,
            **validated_data,
        )

        for experience in experiences_data:
            WorkExperience.objects.create(
                resume=resume,
                **experience,
            )

        for education in education_data:
            Education.objects.create(
                resume=resume,
                **education,
            )

        for skill in skills_data:
            Skill.objects.create(
                resume=resume,
                **skill,
            )

        for project in projects_data:
            Project.objects.create(
                resume=resume,
                **project,
            )

        return resume

    def update(self, instance, validated_data):

        experiences_data = validated_data.pop(
            "experiences",
            None
        )

        education_data = validated_data.pop(
            "education",
            None
        )

        skills_data = validated_data.pop(
            "skills",
            None
        )

        projects_data = validated_data.pop(
            "projects",
            None
        )

        # Update main resume fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Experiences
        if experiences_data is not None:

            instance.experiences.all().delete()

            for experience in experiences_data:
                WorkExperience.objects.create(
                    resume=instance,
                    **experience,
                )

        # Education
        if education_data is not None:

            instance.education.all().delete()

            for education in education_data:
                Education.objects.create(
                    resume=instance,
                    **education,
                )

        # Skills
        if skills_data is not None:

            instance.skills.all().delete()

            for skill in skills_data:
                Skill.objects.create(
                    resume=instance,
                    **skill,
                )

        # Projects
        if projects_data is not None:

            instance.projects.all().delete()

            for project in projects_data:
                Project.objects.create(
                    resume=instance,
                    **project,
                )

        return instance