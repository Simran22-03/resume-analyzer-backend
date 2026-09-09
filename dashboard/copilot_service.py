# dashboard/copilot_service.py

import re

from django.conf import settings
from groq import Groq

from .prompts import build_copilot_prompt


# =========================================================
# RESPONSE CLEANING
# =========================================================

def clean_response(raw_text):
    """
    Clean accidental Markdown while preserving
    the response style.

    Normal answers remain paragraphs.
    Bullets remain bullets.
    Numbered lists are converted to bullets.
    """

    if not raw_text:
        return ""

    raw_text = raw_text.replace(
        "\r\n",
        "\n",
    )

    lines = raw_text.split("\n")

    cleaned_lines = []

    for raw_line in lines:

        line = raw_line.strip()

        if not line:
            if (
                cleaned_lines
                and cleaned_lines[-1] != ""
            ):
                cleaned_lines.append("")

            continue

        # -------------------------------------------------
        # Remove Markdown headings
        # -------------------------------------------------

        line = re.sub(
            r"^\s{0,3}#{1,6}\s*",
            "",
            line,
        )

        # -------------------------------------------------
        # Remove bold / italic markers
        # -------------------------------------------------

        line = line.replace(
            "**",
            "",
        )

        line = line.replace(
            "__",
            "",
        )

        line = re.sub(
            r"(?<!\*)\*([^*]+)\*(?!\*)",
            r"\1",
            line,
        )

        # -------------------------------------------------
        # Remove code fences
        # -------------------------------------------------

        line = line.replace(
            "```",
            "",
        )

        # -------------------------------------------------
        # Markdown table
        # -------------------------------------------------

        if "|" in line:

            cells = [
                cell.strip()
                for cell in line.strip("|").split("|")
            ]

            # Ignore table separator row
            if cells and all(
                re.fullmatch(
                    r":?-{2,}:?",
                    cell or "",
                )
                for cell in cells
            ):
                continue

            cells = [
                cell
                for cell in cells
                if cell
            ]

            if cells:

                table_line = (
                    "- "
                    + " - ".join(cells)
                )

                cleaned_lines.append(
                    table_line
                )

                continue

        # -------------------------------------------------
        # Numbered list
        # -------------------------------------------------

        if re.match(
            r"^\s*\d+[\.\)]\s+",
            line,
        ):

            line = re.sub(
                r"^\s*\d+[\.\)]\s+",
                "- ",
                line,
            )

            cleaned_lines.append(line)

            continue

        # -------------------------------------------------
        # Existing bullet
        # -------------------------------------------------

        if re.match(
            r"^\s*[•●▪◦]\s*",
            line,
        ):

            line = re.sub(
                r"^\s*[•●▪◦]\s*",
                "- ",
                line,
            )

            cleaned_lines.append(line)

            continue

        # -------------------------------------------------
        # Existing dash bullet
        # -------------------------------------------------

        if re.match(
            r"^\s*[-–—]\s+",
            line,
        ):

            line = re.sub(
                r"^\s*[-–—]\s+",
                "- ",
                line,
            )

            cleaned_lines.append(line)

            continue

        # -------------------------------------------------
        # Existing star bullet
        # -------------------------------------------------

        if re.match(
            r"^\s*\*\s+",
            line,
        ):

            line = re.sub(
                r"^\s*\*\s+",
                "- ",
                line,
            )

            cleaned_lines.append(line)

            continue

        # -------------------------------------------------
        # NORMAL TEXT
        # -------------------------------------------------

        cleaned_lines.append(line)

    # =====================================================
    # Remove duplicate blank lines
    # =====================================================

    result = []

    previous_blank = False

    for line in cleaned_lines:

        blank = not line.strip()

        if blank and previous_blank:
            continue

        result.append(
            line.rstrip()
        )

        previous_blank = blank

    return "\n".join(
        result
    ).strip()


# =========================================================
# COPILOT SERVICE
# =========================================================

def chat_with_specific_resume(
    resume_text,
    job_description,
    ats_score,
    strengths,
    missing_skills,
    weaknesses,
    suggestions,
    history,
    user_message,
):
    """
    Generate a Copilot response for exactly one resume.

    History comes from the backend/database.

    The frontend sends only the current user message.
    """

    if not settings.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not configured."
        )

    client = Groq(
        api_key=settings.GROQ_API_KEY
    )

    # =====================================================
    # BUILD PROMPT
    # =====================================================

    prompt = build_copilot_prompt(
        resume_text=resume_text,
        job_description=job_description,
        ats_score=ats_score,
        strengths=strengths,
        missing_skills=missing_skills,
        weaknesses=weaknesses,
        suggestions=suggestions,
        history=history,
        user_message=user_message,
    )

    # =====================================================
    # GROQ REQUEST
    # =====================================================

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.25,
            max_completion_tokens=700,
        )

        if not response.choices:
            raise ValueError(
                "Groq returned no choices."
            )

        content = (
            response.choices[0]
            .message.content
        )

        if not content:
            raise ValueError(
                "Groq returned an empty Copilot response."
            )

        cleaned_response = clean_response(
            content
        )

        if not cleaned_response:
            raise ValueError(
                "Copilot response became empty after formatting."
            )

        print(
            "\n========== COPILOT RESPONSE ==========\n"
        )

        print(
            cleaned_response
        )

        print(
            "\n=======================================\n"
        )

        return cleaned_response

    except Exception as exc:

        print(
            "\n========== COPILOT GROQ ERROR ==========\n"
        )

        print(
            f"{type(exc).__name__}: {exc}"
        )

        print(
            "\n========================================\n"
        )

        raise