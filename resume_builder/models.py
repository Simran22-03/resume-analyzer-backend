from django.conf import settings
from django.db import models


class ResumeBuilder(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="built_resumes",
    )

    title = models.CharField(
        max_length=200,
        default="My Resume",
    )

    full_name = models.CharField(
        max_length=150,
        blank=True,
    )

    professional_title = models.CharField(
        max_length=150,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    location = models.CharField(
        max_length=200,
        blank=True,
    )

    professional_summary = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    is_generated = models.BooleanField(
        default=False,
    )

    def __str__(self):
        return f"{self.user.email} - {self.title}"


class WorkExperience(models.Model):
    resume = models.ForeignKey(
        ResumeBuilder,
        on_delete=models.CASCADE,
        related_name="experiences",
    )

    job_title = models.CharField(
        max_length=150,
    )

    company_name = models.CharField(
        max_length=150,
    )

    location = models.CharField(
        max_length=200,
        blank=True,
    )

    start_date = models.CharField(
        max_length=50,
        blank=True,
    )

    end_date = models.CharField(
        max_length=50,
        blank=True,
    )

    currently_working = models.BooleanField(
        default=False,
    )

    responsibilities = models.TextField(
        blank=True,
    )

    def __str__(self):
        return f"{self.job_title} - {self.company_name}"


class Education(models.Model):
    resume = models.ForeignKey(
        ResumeBuilder,
        on_delete=models.CASCADE,
        related_name="education",
    )

    degree = models.CharField(
        max_length=150,
    )

    institution = models.CharField(
        max_length=200,
    )

    location = models.CharField(
        max_length=200,
        blank=True,
    )

    start_date = models.CharField(
        max_length=50,
        blank=True,
    )

    end_date = models.CharField(
        max_length=50,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    def __str__(self):
        return f"{self.degree} - {self.institution}"


class Skill(models.Model):
    resume = models.ForeignKey(
        ResumeBuilder,
        on_delete=models.CASCADE,
        related_name="skills",
    )

    name = models.CharField(
        max_length=100,
    )

    def __str__(self):
        return self.name


class Project(models.Model):
    resume = models.ForeignKey(
        ResumeBuilder,
        on_delete=models.CASCADE,
        related_name="projects",
    )

    name = models.CharField(
        max_length=150,
    )

    description = models.TextField(
        blank=True,
    )

    technologies = models.CharField(
        max_length=300,
        blank=True,
    )

    project_url = models.URLField(
        blank=True,
    )

    def __str__(self):
        return self.name