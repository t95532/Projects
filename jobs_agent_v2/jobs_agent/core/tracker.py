"""
core/tracker.py
SQLite-backed tracker for all applications submitted by the agent.
"""

from __future__ import annotations
import sqlite3
import datetime
from pathlib import Path


DB_PATH = "data/applications.db"

STATUS_APPLIED = "applied"
STATUS_PENDING_REVIEW = "pending_review"
STATUS_SKIPPED = "skipped"
STATUS_FAILED = "failed"


class Tracker:
    def __init__(self, db_path: str = DB_PATH):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id      TEXT,
                platform    TEXT,
                company     TEXT,
                job_title   TEXT,
                job_url     TEXT,
                status      TEXT,
                notes       TEXT,
                applied_at  TEXT,
                updated_at  TEXT
            )
        """)
        self.conn.commit()

    def already_applied(self, job_id: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM applications WHERE job_id = ? AND status = ?",
            (job_id, STATUS_APPLIED),
        )
        return cur.fetchone() is not None

    def log(
        self,
        job_id: str,
        platform: str,
        company: str,
        job_title: str,
        job_url: str,
        status: str = STATUS_APPLIED,
        notes: str = "",
    ):
        now = datetime.datetime.utcnow().isoformat()
        self.conn.execute(
            """INSERT INTO applications
               (job_id, platform, company, job_title, job_url, status, notes, applied_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (job_id, platform, company, job_title, job_url, status, notes, now, now),
        )
        self.conn.commit()

    def update_status(self, job_id: str, status: str, notes: str = ""):
        now = datetime.datetime.utcnow().isoformat()
        self.conn.execute(
            "UPDATE applications SET status = ?, notes = ?, updated_at = ? WHERE job_id = ?",
            (status, notes, now, job_id),
        )
        self.conn.commit()

    def get_stats(self) -> dict:
        cur = self.conn.execute(
            "SELECT status, COUNT(*) FROM applications GROUP BY status"
        )
        return dict(cur.fetchall())

    def pending_review(self) -> list[dict]:
        cur = self.conn.execute(
            "SELECT * FROM applications WHERE status = ?", (STATUS_PENDING_REVIEW,)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def close(self):
        self.conn.close()
