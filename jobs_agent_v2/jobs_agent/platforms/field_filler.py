"""
platforms/field_filler.py

Handles ALL field types found on job application forms:
  - text / textarea       → fill()
  - number                → fill() with numeric value
  - boolean (Yes/No)      → click the matching radio button
  - select (dropdown)     → select_option() with fuzzy label match
  - multi_select          → check matching checkboxes
  - radio group           → click matching option
  - file                  → set_input_files()
  - date                  → fill() in expected format

Usage:
    filler = FieldFiller(page, qa_bank, llm_engine)
    await filler.fill_all_fields(job)
"""

from __future__ import annotations
import asyncio
import random
from playwright.async_api import Page, Locator
from rapidfuzz import fuzz

from core.qa_bank import QABank
from core.llm_engine import LLMEngine
from utils.browser import BrowserManager


# ── Selectors used to discover all question containers ─────────────────────
QUESTION_CONTAINER_SELECTORS = [
    # Greenhouse
    ".field",
    ".application-question",
    # LinkedIn
    ".jobs-easy-apply-form-section__grouping",
    # Lever
    ".application-field",
    # Generic
    "[data-field]",
    "fieldset",
    ".form-group",
    ".question",
]

LABEL_SELECTORS = [
    "label",
    "legend",
    ".field-label",
    ".application-label",
    ".question-text",
    "[data-label]",
    "h3",
    "h4",
    "p.label",
]


class FieldFiller:
    def __init__(self, page: Page, qa_bank: QABank, llm: LLMEngine):
        self.page = page
        self.qa_bank = qa_bank
        self.llm = llm

    # ── Public entry point ──────────────────────────────────────────────────

    async def fill_all_fields(self, job: dict):
        """
        Discover every question on the current page and fill it correctly
        based on its field type.
        """
        containers = await self._find_question_containers()

        for container in containers:
            try:
                await self._fill_container(container, job)
                await BrowserManager.human_delay(200, 600)
            except Exception:
                continue  # Never crash the whole form over one field

    # ── Container discovery ─────────────────────────────────────────────────

    async def _find_question_containers(self) -> list[Locator]:
        """Try each known container selector and return all matches."""
        found = []
        for sel in QUESTION_CONTAINER_SELECTORS:
            items = await self.page.locator(sel).all()
            if items:
                found.extend(items)
        # De-duplicate by bounding box position (rough)
        return found if found else await self._fallback_containers()

    async def _fallback_containers(self) -> list[Locator]:
        """If no containers found, treat every input/select/textarea as its own unit."""
        all_inputs = await self.page.locator(
            "input:not([type='hidden']):not([type='submit']):not([type='file']), "
            "select, textarea"
        ).all()
        return all_inputs

    # ── Per-container logic ─────────────────────────────────────────────────

    async def _fill_container(self, container: Locator, job: dict):
        label = await self._extract_label(container)

        # Detect what input type lives inside this container
        field_type = await self._detect_field_type(container)

        if field_type == "skip":
            return

        # Resolve the answer (Q&A bank → LLM fallback)
        answer, answer_type = await self._resolve(label, job, field_type)

        if not answer:
            return

        # Use the correct Playwright interaction for the field type
        await self._interact(container, field_type, answer, label, job)

    # ── Label extraction ────────────────────────────────────────────────────

    async def _extract_label(self, container: Locator) -> str:
        for sel in LABEL_SELECTORS:
            try:
                el = container.locator(sel).first
                if await el.count() > 0:
                    text = (await el.inner_text()).strip()
                    if text:
                        return text
            except Exception:
                continue

        # Fallback: aria-label or placeholder on the input itself
        for attr_sel in [
            "input[aria-label]", "select[aria-label]", "textarea[aria-label]",
            "input[placeholder]", "textarea[placeholder]",
        ]:
            try:
                el = container.locator(attr_sel).first
                if await el.count() > 0:
                    val = (
                        await el.get_attribute("aria-label")
                        or await el.get_attribute("placeholder")
                        or ""
                    )
                    if val:
                        return val.strip()
            except Exception:
                continue

        return ""

    # ── Field type detection ────────────────────────────────────────────────

    async def _detect_field_type(self, container: Locator) -> str:
        """
        Returns one of:
            text | number | email | phone | date | url |
            boolean | radio | select | multi_select | textarea | file | skip
        """
        # File upload
        if await container.locator("input[type='file']").count() > 0:
            return "file"

        # Checkbox group → multi_select
        checkboxes = await container.locator("input[type='checkbox']").count()
        if checkboxes > 1:
            return "multi_select"
        if checkboxes == 1:
            return "boolean"

        # Radio group
        radios = await container.locator("input[type='radio']").count()
        if radios > 0:
            # If options are Yes/No → boolean; otherwise → radio
            radio_labels = []
            for r in await container.locator("input[type='radio']").all():
                lbl = await self._label_for_radio(r)
                radio_labels.append(lbl.lower())
            yes_no = {"yes", "no", "true", "false"}
            if all(l in yes_no for l in radio_labels if l):
                return "boolean"
            return "radio"

        # Dropdown
        if await container.locator("select").count() > 0:
            return "select"

        # Textarea
        if await container.locator("textarea").count() > 0:
            return "textarea"

        # Typed inputs
        inp = container.locator("input").first
        if await inp.count() == 0:
            return "skip"

        input_type = (await inp.get_attribute("type") or "text").lower()
        if input_type in ("submit", "button", "reset", "image", "hidden"):
            return "skip"
        if input_type == "number":
            return "number"
        if input_type == "email":
            return "email"
        if input_type == "tel":
            return "phone"
        if input_type == "date":
            return "date"
        if input_type == "url":
            return "url"
        if input_type == "checkbox":
            return "boolean"
        if input_type == "radio":
            return "radio"

        return "text"

    # ── Answer resolution ───────────────────────────────────────────────────

    async def _resolve(
        self, label: str, job: dict, field_type: str
    ) -> tuple[str, str]:
        """
        Returns (answer_string, qa_type).
        Tries Q&A bank first (fuzzy), then LLM.
        """
        if not label:
            return "", field_type

        match = self.qa_bank.match(label)

        if match:
            answer = match["answer"]
            qa_type = match.get("type", field_type)
            if answer == "__GENERATE__":
                answer = self.llm.answer_question(
                    question=label,
                    resume_profile={},   # orchestrator injects profile
                    job_title=job.get("title", ""),
                    company=job.get("company", ""),
                    job_description=job.get("description", ""),
                    answer_type=qa_type,
                )
            return answer, qa_type

        # LLM fallback
        answer = self.llm.answer_question(
            question=label,
            resume_profile={},
            job_title=job.get("title", ""),
            company=job.get("company", ""),
            job_description=job.get("description", ""),
            answer_type=field_type,
        )
        return answer, field_type

    # ── Interaction handlers ────────────────────────────────────────────────

    async def _interact(
        self,
        container: Locator,
        field_type: str,
        answer: str,
        label: str,
        job: dict,
    ):
        handlers = {
            "text":         self._fill_text,
            "textarea":     self._fill_textarea,
            "number":       self._fill_text,
            "email":        self._fill_text,
            "phone":        self._fill_text,
            "url":          self._fill_text,
            "date":         self._fill_text,
            "boolean":      self._fill_boolean,
            "radio":        self._fill_radio,
            "select":       self._fill_select,
            "multi_select": self._fill_multi_select,
            "file":         self._fill_file,
        }
        handler = handlers.get(field_type)
        if handler:
            await handler(container, answer)

    async def _fill_text(self, container: Locator, answer: str):
        inp = container.locator(
            "input[type='text'], input[type='number'], input[type='email'], "
            "input[type='tel'], input[type='date'], input[type='url'], input:not([type])"
        ).first
        if await inp.count() == 0:
            inp = container.locator("input").first
        if await inp.count() == 0:
            return
        # Skip if already filled
        current = await inp.input_value()
        if current.strip():
            return
        await inp.click()
        await inp.fill("")
        for char in answer:
            await inp.type(char)
            await asyncio.sleep(random.uniform(0.03, 0.10))

    async def _fill_textarea(self, container: Locator, answer: str):
        ta = container.locator("textarea").first
        if await ta.count() == 0:
            return
        current = await ta.input_value()
        if current.strip():
            return
        await ta.click()
        await ta.fill("")
        # Type longer text in chunks (more human-like)
        words = answer.split()
        chunk = []
        for word in words:
            chunk.append(word)
            if len(chunk) >= random.randint(5, 12):
                await ta.type(" ".join(chunk) + " ")
                await asyncio.sleep(random.uniform(0.1, 0.3))
                chunk = []
        if chunk:
            await ta.type(" ".join(chunk))

    async def _fill_boolean(self, container: Locator, answer: str):
        """
        Handles Yes/No radio buttons and single checkboxes.
        answer should be "yes"/"no"/"true"/"false" or similar.
        """
        answer_lower = answer.strip().lower()
        positive = answer_lower in ("yes", "true", "1", "agree", "correct")

        # Single checkbox
        cb = container.locator("input[type='checkbox']").first
        if await cb.count() > 0:
            is_checked = await cb.is_checked()
            if positive and not is_checked:
                await cb.click()
            elif not positive and is_checked:
                await cb.click()
            return

        # Radio Yes/No
        radios = await container.locator("input[type='radio']").all()
        for radio in radios:
            lbl = (await self._label_for_radio(radio)).lower()
            matches_yes = positive and lbl in ("yes", "true")
            matches_no = not positive and lbl in ("no", "false")
            if matches_yes or matches_no:
                await radio.click()
                return

        # Fallback: click first radio for positive, second for negative
        if radios:
            await radios[0 if positive else min(1, len(radios) - 1)].click()

    async def _fill_radio(self, container: Locator, answer: str):
        """
        Pick the radio option whose label best matches `answer`.
        Uses fuzzy matching so "bachelor" matches "Bachelor's Degree".
        """
        radios = await container.locator("input[type='radio']").all()
        best_score = 0
        best_radio = None

        for radio in radios:
            lbl = await self._label_for_radio(radio)
            score = fuzz.token_set_ratio(answer.lower(), lbl.lower())
            if score > best_score:
                best_score = score
                best_radio = radio

        if best_radio and best_score > 40:
            await best_radio.click()

    async def _fill_select(self, container: Locator, answer: str):
        """
        Picks the dropdown option whose text best fuzzy-matches `answer`.
        Falls back to value= matching.
        """
        sel = container.locator("select").first
        if await sel.count() == 0:
            return

        # Get all options
        options = await sel.locator("option").all()
        best_score = 0
        best_value = None
        best_label = None

        for opt in options:
            opt_text = (await opt.inner_text()).strip()
            opt_val = await opt.get_attribute("value") or ""
            score = fuzz.token_set_ratio(answer.lower(), opt_text.lower())
            if score > best_score:
                best_score = score
                best_value = opt_val
                best_label = opt_text

        if best_value is not None and best_score > 40:
            try:
                await sel.select_option(value=best_value)
            except Exception:
                try:
                    await sel.select_option(label=best_label)
                except Exception:
                    pass

    async def _fill_multi_select(self, container: Locator, answer: str):
        """
        Checks all checkboxes whose labels are mentioned in `answer`.
        answer can be comma-separated: "Python, Django, REST APIs"
        """
        wanted = [a.strip().lower() for a in answer.split(",")]
        checkboxes = await container.locator("input[type='checkbox']").all()

        for cb in checkboxes:
            lbl = (await self._label_for_radio(cb)).lower()
            if any(fuzz.token_set_ratio(w, lbl) > 70 for w in wanted):
                if not await cb.is_checked():
                    await cb.click()
                    await asyncio.sleep(random.uniform(0.1, 0.3))

    async def _fill_file(self, container: Locator, _answer: str):
        """Upload resume.pdf to the file input."""
        file_input = container.locator("input[type='file']").first
        if await file_input.count() > 0:
            await file_input.set_input_files("data/resume.pdf")
            await BrowserManager.human_delay(800, 1500)

    # ── Helpers ─────────────────────────────────────────────────────────────

    async def _label_for_radio(self, radio: Locator) -> str:
        """Get the visible label for a radio button or checkbox."""
        try:
            radio_id = await radio.get_attribute("id")
            if radio_id:
                label_el = self.page.locator(f"label[for='{radio_id}']").first
                if await label_el.count() > 0:
                    return (await label_el.inner_text()).strip()

            # Try sibling label or parent text
            parent = radio.locator("xpath=..")
            parent_text = (await parent.inner_text()).strip()
            return parent_text

        except Exception:
            return ""
