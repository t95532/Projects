"""
scrapers/greenhouse.py
Fetches job listings from Greenhouse and Lever via their public JSON APIs.
Add target company board slugs to config.yaml under search.greenhouse_boards.
"""

from __future__ import annotations
import httpx


class GreenhouseScraper:
    def __init__(self, config: dict):
        self.config = config
        self.search_cfg = config.get("search", {})
        self.boards: list[str] = self.search_cfg.get("greenhouse_boards", [])
        self.lever_companies: list[str] = self.search_cfg.get("lever_companies", [])

    async def fetch_jobs(self) -> list[dict]:
        jobs = []

        async with httpx.AsyncClient(timeout=15) as client:
            for board_token in self.boards:
                jobs.extend(await self._fetch_greenhouse(client, board_token))

            for company in self.lever_companies:
                jobs.extend(await self._fetch_lever(client, company))

        return self._filter(jobs)

    async def _fetch_greenhouse(self, client: httpx.AsyncClient, board_token: str) -> list[dict]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        try:
            r = await client.get(url)
            data = r.json()
            results = []
            for job in data.get("jobs", []):
                results.append({
                    "job_id": f"greenhouse_{job['id']}",
                    "platform": "greenhouse",
                    "title": job.get("title", ""),
                    "company": board_token,
                    "url": job.get("absolute_url", ""),
                    "location": job.get("location", {}).get("name", ""),
                    "description": job.get("content", ""),
                })
            return results
        except Exception:
            return []

    async def _fetch_lever(self, client: httpx.AsyncClient, company: str) -> list[dict]:
        url = f"https://api.lever.co/v0/postings/{company}?mode=json"
        try:
            r = await client.get(url)
            data = r.json()
            results = []
            for job in data:
                results.append({
                    "job_id": f"lever_{job['id']}",
                    "platform": "greenhouse",  # Same filler handles both
                    "title": job.get("text", ""),
                    "company": company,
                    "url": job.get("hostedUrl", ""),
                    "location": job.get("categories", {}).get("location", ""),
                    "description": job.get("descriptionPlain", ""),
                })
            return results
        except Exception:
            return []

    def _filter(self, jobs: list[dict]) -> list[dict]:
        titles = [t.lower() for t in self.config.get("search", {}).get("job_titles", [])]
        excluded = [k.lower() for k in self.config.get("search", {}).get("keywords_excluded", [])]
        filtered = []
        for job in jobs:
            title_lower = job["title"].lower()
            if titles and not any(t in title_lower for t in titles):
                continue
            if excluded and any(e in title_lower for e in excluded):
                continue
            filtered.append(job)
        return filtered
