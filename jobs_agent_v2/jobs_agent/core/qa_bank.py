"""
core/qa_bank.py
Loads your pre-written answers from qa_bank.yaml and fuzzy-matches
incoming application questions against them.
"""

from __future__ import annotations
import yaml
from rapidfuzz import process, fuzz


FUZZY_THRESHOLD = 72   # 0-100; raise to be stricter


class QABank:
    def __init__(self, path: str = "data/qa_bank.yaml"):
        with open(path) as f:
            entries = yaml.safe_load(f) or []
        self._entries: list[dict] = entries
        self._questions: list[str] = [e["question"] for e in entries]

    def match(self, question: str) -> dict | None:
        """
        Fuzzy-match a question against the bank.
        Returns the entry dict (with .answer, .type) or None if no match.
        """
        if not self._questions:
            return None

        result = process.extractOne(
            question,
            self._questions,
            scorer=fuzz.token_set_ratio,
            score_cutoff=FUZZY_THRESHOLD,
        )
        if result is None:
            return None

        matched_question, score, idx = result
        entry = self._entries[idx]
        return {
            "answer": entry.get("answer", ""),
            "type": entry.get("type", "text"),
            "confidence": score,
            "matched_question": matched_question,
        }

    def all_answers(self) -> list[dict]:
        return self._entries
