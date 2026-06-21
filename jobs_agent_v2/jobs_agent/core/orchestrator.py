"""
core/orchestrator.py
The main agent loop: scrapes jobs, deduplicates, fills forms, tracks results.
"""

from __future__ import annotations
import asyncio
from rich.console import Console
from rich.table import Table

from core.resume_parser import parse_resume
from core.qa_bank import QABank
from core.llm_engine import LLMEngine
from core.tracker import Tracker, STATUS_APPLIED
from utils.browser import BrowserManager

console = Console()


class Orchestrator:
    def __init__(self, config: dict):
        self.config = config
        self.api_key = config["anthropic_api_key"]

        self.resume_profile: dict = {}
        self.qa_bank = QABank("data/qa_bank.yaml")
        self.llm = LLMEngine(self.api_key)
        self.tracker = Tracker()
        self.browser = BrowserManager(
            headless=config.get("browser", {}).get("headless", False),
            slow_mo=config.get("browser", {}).get("slow_mo_ms", 80),
        )

    async def run(self):
        console.rule("[bold]Jobs Auto-Apply Agent[/bold]")

        # 1. Parse resume
        console.print("[cyan]Parsing resume...[/cyan]")
        self.resume_profile = parse_resume("data/resume.pdf", self.api_key)
        console.print(f"  ✓ Profile loaded: {self.resume_profile.get('name')}")

        # 2. Start browser
        console.print("[cyan]Starting browser...[/cyan]")
        await self.browser.start()

        try:
            # 3. Scrape + apply per platform
            platforms = self.config.get("platforms", {})
            max_apps = self.config.get("apply", {}).get("max_per_run", 20)
            applied_count = 0

            if platforms.get("linkedin") and applied_count < max_apps:
                applied_count += await self._run_platform("linkedin", max_apps - applied_count)

            if platforms.get("greenhouse") and applied_count < max_apps:
                applied_count += await self._run_platform("greenhouse", max_apps - applied_count)

            if platforms.get("indeed") and applied_count < max_apps:
                applied_count += await self._run_platform("indeed", max_apps - applied_count)

        finally:
            await self.browser.stop()
            self.tracker.close()

        # 4. Print summary
        self._print_summary()

    async def _run_platform(self, platform: str, limit: int) -> int:
        """Scrape jobs from a platform and apply. Returns number applied."""
        from scrapers.linkedin import LinkedInScraper
        from scrapers.greenhouse import GreenhouseScraper
        from scrapers.indeed import IndeedScraper
        from platforms.linkedin_filler import LinkedInFiller
        from platforms.greenhouse_filler import GreenhouseFiller

        scraper_map = {
            "linkedin": LinkedInScraper,
            "greenhouse": GreenhouseScraper,
            "indeed": IndeedScraper,
        }
        filler_map = {
            "linkedin": LinkedInFiller,
            "greenhouse": GreenhouseFiller,
            "indeed": GreenhouseFiller,  # Indeed uses generic filler
        }

        ScraperClass = scraper_map.get(platform)
        FillerClass = filler_map.get(platform)
        if not ScraperClass or not FillerClass:
            return 0

        console.print(f"\n[bold]{platform.upper()}[/bold]")

        # Scrape jobs
        scraper = ScraperClass(self.config)
        jobs = await scraper.fetch_jobs()
        console.print(f"  Found {len(jobs)} matching jobs")

        # Apply
        page = await self.browser.new_page()
        filler = FillerClass(
            page=page,
            qa_bank=self.qa_bank,
            llm_engine=self.llm,
            tracker=self.tracker,
            resume_profile=self.resume_profile,
            config=self.config,
        )

        # Login once
        logged_in = await filler.login()
        if not logged_in:
            console.print(f"  [red]✗ Login failed for {platform}[/red]")
            return 0

        applied = 0
        for job in jobs[:limit]:
            if self.config.get("apply", {}).get("skip_if_already_applied"):
                if self.tracker.already_applied(job["job_id"]):
                    console.print(f"  [dim]skip (already applied): {job['title']} @ {job['company']}[/dim]")
                    continue

            console.print(f"  → Applying: {job['title']} @ {job['company']}")
            status = await filler.apply(job)

            icon = {"applied": "✓", "skipped": "–", "pending_review": "⚑", "failed": "✗"}.get(status, "?")
            color = {"applied": "green", "skipped": "dim", "pending_review": "yellow", "failed": "red"}.get(status, "white")
            console.print(f"    [{color}]{icon} {status}[/{color}]")

            if status == STATUS_APPLIED:
                applied += 1

            # Human-like delay between applications
            await BrowserManager.human_delay(2000, 5000)

        return applied

    def _print_summary(self):
        stats = self.tracker.get_stats()
        table = Table(title="Run Summary", show_header=True)
        table.add_column("Status")
        table.add_column("Count", justify="right")
        for status, count in stats.items():
            table.add_row(status, str(count))
        console.print(table)

        pending = self.tracker.pending_review()
        if pending:
            console.print(f"\n[yellow]⚑ {len(pending)} applications need your review:[/yellow]")
            for app in pending:
                console.print(f"  • {app['job_title']} @ {app['company']} — {app['job_url']}")
