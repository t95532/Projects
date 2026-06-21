"""
scrapers/linkedin.py
Scrapes LinkedIn job listings matching your search preferences.
Uses LinkedIn's public job search — no API key needed.
"""

from __future__ import annotations
import httpx
from bs4 import BeautifulSoup
import urllib.parse


class LinkedInScraper:
    BASE_URL = "https://www.linkedin.com/jobs/search"

    def __init__(self, config: dict):
        self.config = config
        self.search_cfg = config.get("search", {})

    async def fetch_jobs(self) -> list[dict]:
        jobs = []
        for title in self.search_cfg.get("job_titles", []):
            jobs.extend(await self._search(title))
        return self._filter(jobs)

    async def _search(self, title: str) -> list[dict]:
        location = self.search_cfg.get("location", "")
        params = {
            "keywords": title,
            "location": location,
            "f_AL": "true",   # Easy Apply only
            "sortBy": "DD",   # Most recent
        }
        if self.search_cfg.get("remote"):
            params["f_WT"] = "2"   # Remote filter

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
        }

        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            r = await client.get(url, headers=headers)

        soup = BeautifulSoup(r.text, "lxml")
        results = []

        for card in soup.select(".base-card"):
            try:
                job_id = card.get("data-entity-urn", "").split(":")[-1]
                job_title = card.select_one(".base-search-card__title")
                company = card.select_one(".base-search-card__subtitle")
                job_url = card.select_one("a.base-card__full-link")
                location = card.select_one(".job-search-card__location")

                if not all([job_id, job_title, company, job_url]):
                    continue

                results.append({
                    "job_id": f"linkedin_{job_id}",
                    "platform": "linkedin",
                    "title": job_title.get_text(strip=True),
                    "company": company.get_text(strip=True),
                    "url": job_url["href"].split("?")[0],
                    "location": location.get_text(strip=True) if location else "",
                    "description": "",  # Fetched lazily by filler when needed
                })
            except Exception:
                continue

        return results

    def _filter(self, jobs: list[dict]) -> list[dict]:
        """Apply keyword inclusion/exclusion filters."""
        required = [k.lower() for k in self.search_cfg.get("keywords_required", [])]
        excluded = [k.lower() for k in self.search_cfg.get("keywords_excluded", [])]
        filtered = []
        for job in jobs:
            text = (job["title"] + " " + job.get("description", "")).lower()
            if excluded and any(e in text for e in excluded):
                continue
            filtered.append(job)
        # De-duplicate by job_id
        seen = set()
        unique = []
        for j in filtered:
            if j["job_id"] not in seen:
                seen.add(j["job_id"])
                unique.append(j)
        return unique
