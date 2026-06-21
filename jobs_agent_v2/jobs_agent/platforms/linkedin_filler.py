"""
platforms/linkedin_filler.py
LinkedIn Easy Apply — uses FieldFiller for all form interactions.
"""

from __future__ import annotations
from platforms.base_filler import BaseFiller
from platforms.field_filler import FieldFiller
from utils.browser import BrowserManager


class LinkedInFiller(BaseFiller):

    async def login(self) -> bool:
        creds = self.config.get("credentials", {}).get("linkedin", {})
        await self.page.goto("https://www.linkedin.com/login")
        await self.page.fill("#username", creds.get("email", ""))
        await BrowserManager.human_delay(300, 700)
        await self.page.fill("#password", creds.get("password", ""))
        await BrowserManager.human_delay(400, 900)
        await self.page.click('[type="submit"]')
        await self.page.wait_for_load_state("networkidle")
        return "feed" in self.page.url or "mynetwork" in self.page.url

    async def apply(self, job: dict) -> str:
        if self.should_flag_for_review(job):
            self.tracker.log(**self._log_args(job, "pending_review", "Flagged for review"))
            return "pending_review"

        try:
            await self.page.goto(job["url"])
            await self.page.wait_for_load_state("networkidle")

            easy_apply_btn = self.page.locator("button:has-text('Easy Apply')").first
            if not await easy_apply_btn.is_visible():
                self.tracker.log(**self._log_args(job, "skipped", "No Easy Apply button"))
                return "skipped"

            await easy_apply_btn.click()
            await BrowserManager.human_delay()

            filler = FieldFiller(self.page, self.qa_bank, self.llm)
            await self._walk_modal(filler, job)

            self.tracker.log(**self._log_args(job, "applied"))
            return "applied"

        except Exception as e:
            self.tracker.log(**self._log_args(job, "failed", str(e)))
            return "failed"

    async def _walk_modal(self, filler: FieldFiller, job: dict):
        """Step through the Easy Apply multi-page modal."""
        for _ in range(12):   # max 12 steps
            await BrowserManager.human_delay(600, 1200)

            # Fill everything on this step
            await filler.fill_all_fields(job)

            # Progress buttons
            submit_btn  = self.page.locator("button:has-text('Submit application')").first
            review_btn  = self.page.locator("button:has-text('Review')").first
            next_btn    = self.page.locator("button:has-text('Next')").first

            if await submit_btn.is_visible():
                await submit_btn.click()
                return
            elif await review_btn.is_visible():
                await review_btn.click()
            elif await next_btn.is_visible():
                await next_btn.click()
            else:
                break

    def _log_args(self, job: dict, status: str, notes: str = "") -> dict:
        return dict(
            job_id=job["job_id"], platform="linkedin",
            company=job.get("company", ""), job_title=job.get("title", ""),
            job_url=job.get("url", ""), status=status, notes=notes,
        )
