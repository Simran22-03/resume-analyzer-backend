import json
import os
import re

from langchain_groq import ChatGroq

from .prompts import (
    QUESTION_GENERATION_PROMPT,
    ANSWER_EVALUATION_PROMPT,
    QUICK_PRACTICE_QUESTION_PROMPT,
    QUICK_PRACTICE_ANSWER_PROMPT,
)


MODEL = "openai/gpt-oss-120b"


# ============================================================
# GROQ MODEL
# ============================================================

def get_groq_model():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not configured."
        )

    return ChatGroq(
        api_key=api_key,
        model=MODEL,
        temperature=0.3,
    )


# ============================================================
# CLEAN GROQ JSON RESPONSE
# ============================================================

def _clean_json_response(content):
    """
    Clean Groq response and extract JSON.
    """

    if isinstance(content, list):
        content = "".join(
            str(item)
            for item in content
        )

    content = str(content).strip()

    content = re.sub(
        r"^```(?:json)?\s*",
        "",
        content,
        flags=re.IGNORECASE,
    )

    content = re.sub(
        r"\s*```$",
        "",
        content,
    )

    content = content.strip()

    first_brace = content.find("{")
    last_brace = content.rfind("}")

    if (
        first_brace != -1
        and last_brace != -1
        and last_brace > first_brace
    ):
        content = content[
            first_brace:last_brace + 1
        ]

    return content.strip()


# ============================================================
# NORMALIZE QUESTIONS
# ============================================================

def _normalize_questions(
    questions,
    total_questions,
):
    """
    Clean Groq-generated questions and guarantee
    exactly the requested number.
    """

    if not isinstance(
        questions,
        list,
    ):
        raise ValueError(
            "Groq returned an invalid questions list."
        )

    cleaned = []

    seen_questions = set()

    for item in questions:

        if not isinstance(
            item,
            dict,
        ):
            continue

        question = str(
            item.get(
                "question",
                "",
            )
        ).strip()

        category = str(
            item.get(
                "category",
                "General",
            )
        ).strip()

        if not question:
            continue

        normalized_key = (
            re.sub(
                r"\s+",
                " ",
                question.lower(),
            )
            .strip()
        )

        if normalized_key in seen_questions:
            continue

        seen_questions.add(
            normalized_key
        )

        cleaned.append(
            {
                "category": (
                    category
                    or "General"
                ),
                "question": question,
            }
        )

    if len(cleaned) < total_questions:
        raise ValueError(
            f"Groq returned only "
            f"{len(cleaned)} valid questions. "
            f"Expected {total_questions}."
        )

    cleaned = cleaned[
        :total_questions
    ]

    return cleaned


# ============================================================
# HELPER - FORMAT PROMPT
# ============================================================

def _format_prompt(
    prompt,
    replacements,
):
    """
    Replace prompt placeholders safely.

    This intentionally uses simple string replacement
    instead of LangChain PromptTemplate so JSON braces
    inside prompts do not cause template-variable errors.
    """

    formatted_prompt = prompt

    for key, value in replacements.items():

        formatted_prompt = formatted_prompt.replace(
            "{" + key + "}",
            str(value if value is not None else ""),
        )

    return formatted_prompt


# ============================================================
# GENERATE FULL INTERVIEW QUESTIONS
# ============================================================

def generate_interview_questions(
    interview_type,
    target_role,
    experience_level,
    experience_duration="",
    custom_interview_type="",
    technical_topic=None,
    total_questions=30,
):
    """
    Generate questions for the complete interview.

    Existing function signature is preserved.
    """

    try:
        total_questions = int(
            total_questions or 30
        )

    except (
        TypeError,
        ValueError,
    ):
        total_questions = 30

    total_questions = max(
        1,
        min(
            total_questions,
            50,
        ),
    )

    # --------------------------------------------------------
    # USE FULL INTERVIEW PROMPT
    # --------------------------------------------------------

    prompt = _format_prompt(
        QUESTION_GENERATION_PROMPT,
        {
            "interview_type": interview_type,
            "custom_interview_type": (
                custom_interview_type
                or "Not specified"
            ),
            "target_role": (
                target_role
                or "Software Developer"
            ),
            "experience_level": (
                experience_level
                or "fresher"
            ),
            "experience_duration": (
                experience_duration
                or "Not specified"
            ),
            "technical_topic": (
                technical_topic
                or "Not specified"
            ),
            "total_questions": total_questions,
        },
    )

    # --------------------------------------------------------
    # CALL GROQ
    # --------------------------------------------------------

    model = get_groq_model()

    response = model.invoke(
        prompt
    )

    content = _clean_json_response(
        response.content
    )

    # --------------------------------------------------------
    # PARSE JSON
    # --------------------------------------------------------

    try:

        data = json.loads(
            content
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Groq returned invalid JSON while "
            "generating interview questions."
        ) from exc

    questions = data.get(
        "questions",
        [],
    )

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

    cleaned_questions = (
        _normalize_questions(
            questions,
            total_questions,
        )
    )

    if len(cleaned_questions) != total_questions:

        raise ValueError(
            f"Expected {total_questions} questions, "
            f"got {len(cleaned_questions)}."
        )

    return cleaned_questions


# ============================================================
# EVALUATE FULL INTERVIEW ANSWER
# ============================================================

def evaluate_interview_answer(
    question,
    answer,
    category="General",
    interview_type=None,
    target_role=None,
    experience_level=None,
):
    """
    Evaluate an answer from the complete interview.
    """

    prompt = _format_prompt(
        ANSWER_EVALUATION_PROMPT,
        {
            "question": question,
            "answer": answer,
            "category": category or "General",
            "interview_type": (
                interview_type
                or "Not specified"
            ),
            "target_role": (
                target_role
                or "Not specified"
            ),
            "experience_level": (
                experience_level
                or "Not specified"
            ),
        },
    )

    model = get_groq_model()

    response = model.invoke(
        prompt
    )

    content = _clean_json_response(
        response.content
    )

    try:

        evaluation = json.loads(
            content
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Groq returned invalid evaluation JSON."
        ) from exc

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = evaluation.get(
        "score",
        0,
    )

    try:

        score = float(score)

    except (
        TypeError,
        ValueError,
    ):
        score = 0

    score = max(
        0,
        min(
            100,
            score,
        ),
    )

    # --------------------------------------------------------
    # COMMUNICATION SCORE
    # --------------------------------------------------------

    communication_score = (
        evaluation.get(
            "communication_score",
            0,
        )
    )

    try:

        communication_score = float(
            communication_score
        )

    except (
        TypeError,
        ValueError,
    ):
        communication_score = 0

    communication_score = max(
        0,
        min(
            100,
            communication_score,
        ),
    )

    # --------------------------------------------------------
    # PROBLEM SOLVING SCORE
    # --------------------------------------------------------

    problem_solving_score = (
        evaluation.get(
            "problem_solving_score",
            0,
        )
    )

    try:

        problem_solving_score = float(
            problem_solving_score
        )

    except (
        TypeError,
        ValueError,
    ):
        problem_solving_score = 0

    problem_solving_score = max(
        0,
        min(
            100,
            problem_solving_score,
        ),
    )

    # --------------------------------------------------------
    # STRENGTHS
    # --------------------------------------------------------

    strengths = evaluation.get(
        "strengths",
        [],
    )

    if not isinstance(
        strengths,
        list,
    ):
        strengths = []

    # --------------------------------------------------------
    # IMPROVEMENTS
    # --------------------------------------------------------

    improvements = evaluation.get(
        "improvements",
        [],
    )

    if not isinstance(
        improvements,
        list,
    ):
        improvements = []

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "score": score,

        "feedback": str(
            evaluation.get(
                "feedback",
                "",
            )
        ),

        "strengths": strengths,

        "improvements": improvements,

        "communication_score": (
            communication_score
        ),

        "problem_solving_score": (
            problem_solving_score
        ),
    }


# ============================================================
# QUICK PRACTICE - QUESTION GENERATION
# ============================================================

def generate_quick_practice_questions(
    practice_type="technical",
    target_role="Software Engineer",
    topic="",
    difficulty="medium",
    question_count=5,
):
    """
    Generate questions specifically for Quick Practice.

    Uses a separate prompt from Full Interview.
    """

    try:

        question_count = int(
            question_count or 5
        )

    except (
        TypeError,
        ValueError,
    ):

        question_count = 5

    question_count = max(
        1,
        min(
            question_count,
            20,
        ),
    )

    # --------------------------------------------------------
    # USE QUICK PRACTICE PROMPT
    # --------------------------------------------------------

    prompt = _format_prompt(
        QUICK_PRACTICE_QUESTION_PROMPT,
        {
            "practice_type": (
                practice_type
                or "technical"
            ),
            "target_role": (
                target_role
                or "Software Engineer"
            ),
            "topic": (
                topic
                or "General"
            ),
            "difficulty": (
                difficulty
                or "medium"
            ),
            "question_count": question_count,
        },
    )

    # --------------------------------------------------------
    # CALL GROQ
    # --------------------------------------------------------

    model = get_groq_model()

    response = model.invoke(
        prompt
    )

    content = _clean_json_response(
        response.content
    )

    # --------------------------------------------------------
    # PARSE JSON
    # --------------------------------------------------------

    try:

        data = json.loads(
            content
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Groq returned invalid JSON for "
            "Quick Practice."
        ) from exc

    questions = data.get(
        "questions",
        [],
    )

    # --------------------------------------------------------
    # NORMALIZE
    # --------------------------------------------------------

    return _normalize_questions(
        questions,
        question_count,
    )


# ============================================================
# QUICK PRACTICE - ANSWER EVALUATION
# ============================================================

def evaluate_quick_practice_answer(
    question,
    answer,
    category="General",
    practice_type="technical",
):
    """
    Evaluate Quick Practice answers using the dedicated
    Quick Practice evaluation prompt.
    """

    prompt = _format_prompt(
        QUICK_PRACTICE_ANSWER_PROMPT,
        {
            "question": question,
            "answer": answer,
            "category": (
                category
                or "General"
            ),
            "practice_type": (
                practice_type
                or "technical"
            ),
        },
    )

    model = get_groq_model()

    response = model.invoke(
        prompt
    )

    content = _clean_json_response(
        response.content
    )

    # --------------------------------------------------------
    # PARSE JSON
    # --------------------------------------------------------

    try:

        evaluation = json.loads(
            content
        )

    except json.JSONDecodeError as exc:

        raise ValueError(
            "Groq returned invalid evaluation JSON "
            "for Quick Practice."
        ) from exc

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = evaluation.get(
        "score",
        0,
    )

    try:

        score = float(score)

    except (
        TypeError,
        ValueError,
    ):
        score = 0

    score = max(
        0,
        min(
            100,
            score,
        ),
    )

    # --------------------------------------------------------
    # COMMUNICATION SCORE
    # --------------------------------------------------------

    communication_score = (
        evaluation.get(
            "communication_score",
            0,
        )
    )

    try:

        communication_score = float(
            communication_score
        )

    except (
        TypeError,
        ValueError,
    ):
        communication_score = 0

    communication_score = max(
        0,
        min(
            100,
            communication_score,
        ),
    )

    # --------------------------------------------------------
    # PROBLEM SOLVING SCORE
    # --------------------------------------------------------

    problem_solving_score = (
        evaluation.get(
            "problem_solving_score",
            0,
        )
    )

    try:

        problem_solving_score = float(
            problem_solving_score
        )

    except (
        TypeError,
        ValueError,
    ):
        problem_solving_score = 0

    problem_solving_score = max(
        0,
        min(
            100,
            problem_solving_score,
        ),
    )

    # --------------------------------------------------------
    # STRENGTHS
    # --------------------------------------------------------

    strengths = evaluation.get(
        "strengths",
        [],
    )

    if not isinstance(
        strengths,
        list,
    ):
        strengths = []

    # --------------------------------------------------------
    # IMPROVEMENTS
    # --------------------------------------------------------

    improvements = evaluation.get(
        "improvements",
        [],
    )

    if not isinstance(
        improvements,
        list,
    ):
        improvements = []

    # --------------------------------------------------------
    # RETURN SAME RESPONSE STRUCTURE
    # --------------------------------------------------------

    return {
        "score": score,

        "feedback": str(
            evaluation.get(
                "feedback",
                "",
            )
        ),

        "strengths": strengths,

        "improvements": improvements,

        "communication_score": (
            communication_score
        ),

        "problem_solving_score": (
            problem_solving_score
        ),
    }