import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from .prompts import PROFESSIONAL_SUMMARY_PROMPT


load_dotenv(override=True)


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

MODEL = "qwen/qwen3.6-27b"


def generate_professional_summary(
    *,
    job_description: str,
    name: str = "",
    professional_title: str = "",
    skills: str = "",
    experience: str = "",
    education: str = "",
    projects: str = "",
) -> str:

    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not configured."
        )

    if not job_description.strip():
        raise ValueError(
            "Job description is required."
        )

    llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=MODEL,
        temperature=0.4,
        max_tokens=300,
        reasoning_format="hidden",
        reasoning_effort="none",
    )

    prompt = PROFESSIONAL_SUMMARY_PROMPT.format(
        name=name,
        professional_title=professional_title,
        skills=skills or "Not provided",
        experience=experience or "Not provided",
        education=education or "Not provided",
        projects=projects or "Not provided",
        job_description=job_description,
    )

    response = llm.invoke(prompt)

    summary = response.content

    if isinstance(summary, list):
        summary = "".join(
            item.get("text", "")
            for item in summary
            if isinstance(item, dict)
        )

    summary = str(summary).strip()

    print("\n========== GROQ DEBUG ==========")
    print("Model:", MODEL)
    print("Summary length:", len(summary))
    print("Summary:", summary)
    print("================================\n")

    if not summary:
        raise ValueError(
            "Groq returned an empty summary."
        )

    # Safety cleanup in case the model still returns thinking tags
    if "<think>" in summary:
        summary = summary.split("</think>")[-1].strip()

    if summary.startswith("```"):
        summary = (
            summary
            .replace("```text", "")
            .replace("```", "")
            .strip()
        )

    return summary