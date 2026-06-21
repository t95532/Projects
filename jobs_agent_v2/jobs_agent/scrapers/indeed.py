"""
scrapers/indeed.py
Indeed job scraper.
Note: Indeed's HTML structure changes frequently — this is a starting point.
For production use, consider the Indeed Publisher API or a scraping service.
"""

from __future__ import annotations
import urllib.parse
import httpx
from bs4 import BeautifulSoup


class IndeedScraper:
    BASE_URL = "https://www.indeed.com/jobs"

    def __init__(self, config: dict):
        self.config = config
        self.search_cfg = config.get("search", {})

    async def fetch_jobs(self) -> list[dict]:
        jobs = []
        for title in self.search_cfg.get("job_titles", []):
            jobs.extend(await self._search(title))
        return self._deduplicate(jobs)

    async def _search(self, title: str) -> list[dict]:
        params = {
            "q": title,
            "l": self.search_cfg.get("location", ""),
            "sort": "date",
        }
        if self.search_cfg.get("remote"):
            params["remotejob"] = "1"

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                r = await client.get(url, headers=headers)
            soup = BeautifulSoup(r.text, "lxml")
            results = []

            for card in soup.select('[data-jk]'):
                try:
                    job_key = card.get("data-jk", "")
                    title_el = card.select_one(".jobTitle span")
                    company_el = card.select_one(".companyName")
                    location_el = card.select_one(".companyLocation")

                    if not job_key or not title_el:
                        continue

                    results.append({
                        "job_id": f"indeed_{job_key}",
                        "platform": "indeed",
                        "title": title_el.get_text(strip=True),
                        "company": company_el.get_text(strip=True) if company_el else "",
                        "url": f"https://www.indeed.com/viewjob?jk={job_key}",
                        "location": location_el.get_text(strip=True) if location_el else "",
                        "description": "",
                    })
                except Exception:
                    continue

            return results
        except Exception:
            return []

    def _deduplicate(self, jobs: list[dict]) -> list[dict]:
        seen = set()
        unique = []
        for j in jobs:
            if j["job_id"] not in seen:
                seen.add(j["job_id"])
                unique.append(j)
        return unique
