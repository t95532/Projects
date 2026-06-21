"""
core/resume_parser.py
Extracts structured profile data from a PDF or DOCX resume.
Uses Claude to produce clean JSON — no brittle regex.
"""

from __future__ import annotations
import json
import pathlib
import anthropic
import pdfplumber
import docx


def _extract_text(path: str) -> str:
    """Pull raw text from PDF or DOCX."""
    p = pathlib.Path(path)
    if p.suffix.lower() == ".pdf":
        with pdfplumber.open(p) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif p.suffix.lower() in (".docx", ".doc"):
        doc = docx.Document(p)
        return "\n".join(para.text for para in doc.paragraphs)
    else:
        raise ValueError(f"Unsupported resume format: {p.suffix}")


def parse_resume(path: str, api_key: str) -> dict:
    """
    Parse a resume into structured JSON using Claude.

    Returns a dict with keys:
        name, email, phone, location, linkedin, github,
        summary, skills, experience, education, certifications, languages
    """
    raw_text = _extract_text(path)

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Extract structured information from the resume below.
Return ONLY valid JSON with these exact keys:
{{
  "name": "",
  "email": "",
  "phone": "",
  "location": "",
  "linkedin": "",
  "github": "",
  "summary": "",
  "skills": ["skill1", "skill2"],
  "experience": [
    {{
      "company": "",
      "title": "",
      "start_date": "",
      "end_date": "",
      "current": false,
      "description": "",
      "achievements": []
    }}
  ],
  "education": [
    {{
      "institution": "",
      "degree": "",
      "field": "",
      "graduation_year": ""
    }}
  ],
  "certifications": [],
  "languages": [],
  "years_of_experience": 0
}}

RESUME TEXT:
{raw_text}
"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
