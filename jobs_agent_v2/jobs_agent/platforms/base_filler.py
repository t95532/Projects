"""
platforms/base_filler.py
Abstract base class for all platform-specific form fillers.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from playwright.async_api import Page

from core.qa_bank import QABank
from core.llm_engine import LLMEngine
from core.tracker import Tracker


class BaseFiller(ABC):
    """
    Every platform filler must implement:
      - login()
      - find_apply_button()
      - fill_form()
      - submit()
    """

    def __init__(
        self,
        page: Page,
        qa_bank: QABank,
        llm_engine: LLMEngine,
        tracker: Tracker,
        resume_profile: dict,
        config: dict,
    ):
        self.page = page
        self.qa_bank = qa_bank
        self.llm = llm_engine
        self.tracker = tracker
        self.profile = resume_profile
        self.config = config

    @abstractmethod
    async def login(self) -> bool:
        """Log in to the platform. Returns True on success."""
        ...

    @abstractmethod
    async def apply(self, job: dict) -> str:
        """
        Apply to a single job.
        job dict keys: job_id, title, company, url, description
        Returns: 'applied' | 'skipped' | 'pending_review' | 'failed'
        """
        ...

    async def resolve_answer(
        self,
        question: str,
        job: dict,
        answer_type: str = "text",
    ) -> str:
        """
        Try Q&A bank first; fall back to LLM.
        Returns the answer string.
        """
        match = self.qa_bank.match(question)

        if match and match["answer"] != "__GENERATE__":
            return match["answer"]

        # Generate with LLM
        return self.llm.answer_question(
            question=question,
            resume_profile=self.profile,
            job_title=job.get("title", ""),
            company=job.get("company", ""),
            job_description=job.get("description", ""),
            answer_type=answer_type,
        )

    def should_flag_for_review(self, job: dict) -> bool:
        """Return True if this application should be queued for human review."""
        flags = self.config.get("apply", {}).get("require_human_review_for", [])
        desc = (job.get("description", "") + " " + job.get("title", "")).lower()
        return any(f.lower() in desc for f in flags)
