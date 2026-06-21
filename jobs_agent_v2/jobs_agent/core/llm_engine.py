"""
core/llm_engine.py
Uses Claude to generate answers for questions not found in the Q&A bank,
and to produce tailored cover letter snippets.
"""

from __future__ import annotations
import anthropic


class LLMEngine:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def answer_question(
        self,
        question: str,
        resume_profile: dict,
        job_title: str,
        company: str,
        job_description: str = "",
        answer_type: str = "text",
        max_words: int = 80,
    ) -> str:
        """
        Generate an answer to an application question using
        the candidate's resume and the job context.
        """
        profile_summary = self._profile_to_text(resume_profile)

        prompt = f"""You are filling out a job application on behalf of a candidate.

CANDIDATE PROFILE:
{profile_summary}

JOB: {job_title} at {company}
JOB DESCRIPTION SNIPPET: {job_description[:600] if job_description else "Not provided"}

APPLICATION QUESTION: {question}

ANSWER TYPE: {answer_type}
MAX LENGTH: {max_words} words

Rules:
- Answer in first person as the candidate
- Be specific, honest, and concise
- If it's a yes/no question, answer with just Yes or No
- If it's a number question, answer with just a number
- Do NOT make up facts not supported by the profile
- Do NOT include any preamble — just the answer itself
"""

        msg = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()

    def generate_cover_letter(
        self,
        resume_profile: dict,
        job_title: str,
        company: str,
        job_description: str,
    ) -> str:
        """Generate a short tailored cover letter (3-4 paragraphs)."""
        profile_summary = self._profile_to_text(resume_profile)

        prompt = f"""Write a concise, tailored cover letter for this application.

CANDIDATE PROFILE:
{profile_summary}

APPLYING FOR: {job_title} at {company}
JOB DESCRIPTION:
{job_description[:1500]}

Requirements:
- 3 paragraphs max
- Specific to this company and role
- Highlight 2-3 most relevant experiences
- Professional but not stiff
- No generic filler phrases like "I am writing to express my interest"
- End with a clear call to action
- Do NOT include date, address headers, or "Sincerely" boilerplate
"""

        msg = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()

    def _profile_to_text(self, profile: dict) -> str:
        parts = [
            f"Name: {profile.get('name', '')}",
            f"Summary: {profile.get('summary', '')}",
            f"Skills: {', '.join(profile.get('skills', [])[:20])}",
            f"Years of experience: {profile.get('years_of_experience', '')}",
        ]
        for exp in profile.get("experience", [])[:3]:
            parts.append(
                f"- {exp.get('title')} at {exp.get('company')} "
                f"({exp.get('start_date')} – {exp.get('end_date', 'Present')}): "
                f"{exp.get('description', '')[:200]}"
            )
        for edu in profile.get("education", []):
            parts.append(
                f"Education: {edu.get('degree')} in {edu.get('field')} "
                f"from {edu.get('institution')} ({edu.get('graduation_year')})"
            )
        return "\n".join(parts)
