# Jobs Auto-Apply Agent

An end-to-end AI agent that reads your resume, understands job application questions, and automatically fills + submits applications on LinkedIn Easy Apply, Indeed, Greenhouse/Lever, and company career pages.

## Project Structure

```
jobs_agent/
├── main.py                  # Entry point — run the agent
├── config.yaml              # Your preferences, credentials, filters
├── requirements.txt
│
├── core/
│   ├── resume_parser.py     # Extracts structured data from your PDF/DOCX resume
│   ├── qa_bank.py           # Loads & matches your pre-written Q&A answers
│   ├── llm_engine.py        # Claude-powered reasoning — generates answers for unknown questions
│   ├── tracker.py           # SQLite-backed application tracker
│   └── orchestrator.py      # Coordinates the full apply loop
│
├── scrapers/
│   ├── linkedin.py          # LinkedIn Easy Apply scraper
│   ├── indeed.py            # Indeed job scraper
│   ├── greenhouse.py        # Greenhouse/Lever ATS scraper
│   └── career_pages.py      # Generic company career page scraper
│
├── platforms/
│   ├── base_filler.py       # Abstract base class for form fillers
│   ├── linkedin_filler.py   # LinkedIn Easy Apply form automation
│   ├── indeed_filler.py     # Indeed form automation
│   ├── greenhouse_filler.py # Greenhouse/Lever form automation
│   └── generic_filler.py    # Generic HTML form filler
│
├── data/
│   ├── resume.pdf           # Your resume (drop it here)
│   ├── qa_bank.yaml         # Your pre-written answers
│   └── applications.db      # SQLite tracker (auto-created)
│
└── utils/
    ├── browser.py           # Playwright browser manager
    └── helpers.py           # Shared utilities
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Drop your resume in data/resume.pdf

# 3. Fill out data/qa_bank.yaml with your answers

# 4. Configure config.yaml (job titles, salary, location, etc.)

# 5. Run!
python main.py
```

## How It Works

1. **Scraper** finds job listings matching your preferences
2. **Resume Parser** extracts your structured profile (skills, experience, education)
3. **Q&A Bank** fuzzy-matches known questions to your pre-written answers
4. **LLM Engine** (Claude) generates answers for any question not in your bank
5. **Form Filler** uses Playwright to navigate and fill the application
6. **Tracker** logs every application to SQLite with status, date, and job details
7. **Human Review Queue** — anything uncertain gets flagged for your review
