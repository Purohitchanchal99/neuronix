"""Unknown term persistence + simple analytics.

This is deterministic and LLM-free.

Stores low-confidence/unmatched user terms/phrases into data/unknown_terms.json.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "unknown_terms.json"


@dataclass
class UnknownTermEvent:
    query: str
    normalized: str
    top_match: Optional[str]
    score: float
    timestamp: float


class UnknownTermsStore:
    def __init__(self, path: Path = DATA_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self, rows: List[Dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    def append(self, event: UnknownTermEvent) -> None:
        rows = self._load()
        rows.append(asdict(event))
        self._save(rows)

    def stats(self, limit: int = 1000) -> Dict[str, Any]:
        rows = self._load()[-limit:]
        return {
            "count": len(rows),
            "last_timestamp": rows[-1]["timestamp"] if rows else None,
            "avg_score": (sum(float(r.get("score", 0)) for r in rows) / len(rows)) if rows else None,
        }

