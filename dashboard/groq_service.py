import json

from django.conf import settings
from groq import Groq

from .prompts import (
    ANALYSIS_SYSTEM_PROMPT,
    build_analysis_user_prompt,
)


# =========================================================
# RESUME ANALYSIS RESPONSE SCHEMA
# =========================================================

ANALYSIS_SCHEMA = {
    "type": "object",

    "properties": {
        "ats_score": {
            "type": "integer"
        },

        "strengths": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "missing_skills": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "weaknesses": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },

        "suggestions": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },

    "required": [
        "ats_score",
        "strengths",
        "missing_skills",
        "weaknesses",
        "suggestions"
    ],

    "additionalProperties": False
}


# =========================================================
# RESUME ANALYSIS
# =========================================================

def analyze_resume(resume_text, job_description):

    if not settings.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not configured."
        )

    client = Groq(
        api_key=settings.GROQ_API_KEY
    )

    user_prompt = build_analysis_user_prompt(
        resume_text,
        job_description
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "system",
                "content": ANALYSIS_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],

        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "resume_analysis",
                "strict": True,
                "schema": ANALYSIS_SCHEMA
            }
        }
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError(
            "Groq returned an empty response."
        )

    return json.loads(content)