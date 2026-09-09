PROFESSIONAL_SUMMARY_PROMPT = """
Write a professional resume summary for the candidate.

Use the candidate information and target job description below.

Rules:
- Return ONLY the final professional summary.
- Do not explain your answer.
- Do not show your reasoning.
- Do not write <think> tags.
- Do not repeat these instructions.
- Do not mention the prompt.
- Do not mention "candidate information".
- Do not use headings.
- Do not use bullet points.
- Do not use quotation marks.
- Write exactly 3 to 4 professional sentences.
- Keep it ATS-friendly.
- Use only information actually provided.
- Never invent skills, experience, companies, technologies, education, certifications, achievements, or years of experience.
- If the candidate has limited experience, focus on their actual skills, education, and projects.

Candidate Name:
{name}

Professional Title:
{professional_title}

Skills:
{skills}

Work Experience:
{experience}

Education:
{education}

Projects:
{projects}

Target Role / Job Description:
{job_description}

Return ONLY the final resume summary.
"""