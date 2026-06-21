"""
platforms/greenhouse_filler.py
Greenhouse and Lever ATS — uses FieldFiller for all form interactions.
"""

from __future__ import annotations
from platforms.base_filler import BaseFiller
from platforms.field_filler import FieldFiller
from utils.browser import BrowserManager


class GreenhouseFiller(BaseFiller):

    async def login(self) -> bool:
        return True   # Public ATS — no login

    async def apply(self, job: dict) -> str:
        if self.should_flag_for_review(job):
            self.tracker.log(**self._log_args(job, "pending_review", "Flagged for review"))
            return "pending_review"

        try:
            await self.page.goto(job["url"])
            await self.page.wait_for_load_state("networkidle")

            filler = FieldFiller(self.page, self.qa_bank, self.llm)

            # Fill personal info fields first (fixed selectors, faster)
            await self._fill_personal_info()

            # Upload resume
            await self._upload_resume()

            # Fill all dynamic Q&A fields
            await filler.fill_all_fields(job)

            # Submit
            submit = self.page.locator(
                "input[type='submit'], button[type='submit'], "
                "button:has-text('Submit'), button:has-text('Apply')"
            ).first
            if await submit.is_visible():
                await submit.click()
                await self.page.wait_for_load_state("networkidle")

            self.tracker.log(**self._log_args(job, "applied"))
            return "applied"

        except Exception as e:
            self.tracker.log(**self._log_args(job, "failed", str(e)))
            return "failed"

    async def _fill_personal_info(self):
        """Fill standard personal info fields by known selectors."""
        field_map = {
            # Greenhouse selectors
            "#first_name":              self.profile.get("name", "").split()[0],
            "#last_name":               " ".join(self.profile.get("name", "").split()[1:]),
            "#email":                   self.profile.get("email", ""),
            "#phone":                   self.profile.get("phone", ""),
            "#job_application_linkedin_profile_url": self.profile.get("linkedin", ""),
            # Lever selectors
            "input[name='name']":       self.profile.get("name", ""),
            "input[name='email']":      self.profile.get("email", ""),
            "input[name='phone']":      self.profile.get("phone", ""),
            "input[name='urls[LinkedIn]']": self.profile.get("linkedin", ""),
            "input[name='urls[GitHub]']":   self.profile.get("github", ""),
        }
        for selector, value in field_map.items():
            if not value:
                continue
            try:
                el = self.page.locator(selector).first
                if await el.is_visible():
                    current = await el.input_value()
                    if not current.strip():
                        await el.fill(value)
                        await BrowserManager.human_delay(100, 300)
            except Exception:
                continue

    async def _upload_resume(self):
        file_input = self.page.locator("input[type='file']").first
        if await file_input.count() > 0:
            await file_input.set_input_files("data/resume.pdf")
            await BrowserManager.human_delay(1000, 2000)

    def _log_args(self, job: dict, status: str, notes: str = "") -> dict:
        return dict(
            job_id=job["job_id"], platform="greenhouse",
            company=job.get("company", ""), job_title=job.get("title", ""),
            job_url=job.get("url", ""), status=status, notes=notes,
        )
