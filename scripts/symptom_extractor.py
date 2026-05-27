"""Local Symptom Extractor (LLM-free)

Extracts structured understanding from a user query:
- sleep issues
- appetite changes
- fatigue
- concentration issues
- sadness
- duration

Designed as deterministic pattern-based extraction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import re


@dataclass
class SymptomExtraction:
    symptoms: Dict[str, float]
    duration_days: Optional[float]
    matched_signals: Dict[str, str]


class LocalSymptomExtractor:
    def __init__(self):
        # keyword/pattern map for each symptom
        self._patterns = {
            "sleep_issue": [
                r"\b(insomnia|can't\s+sleep|cannot\s+sleep|sleep\s+trouble|poor\s+sleep)\b",
                r"\b(waking\s+up\s+often|early\s+morning\s+waking)\b",
                r"\b(night\s+thoughts|can't\s+shut\s+mind)\b",
            ],
            "appetite_change": [
                r"\b(no\s+appetite|can't\s+eat|eat\s+less)\b",
                r"\b(binge\s+eating|overeating)\b",
                r"\b(appetite\s+changed|appetite\s+gone)\b",
            ],
            "fatigue": [
                r"\b(tired|fatigue|exhausted|low\s+energy|no\s+energy)\b",
                r"\b(sleepy|drained)\b",
            ],
            "concentration": [
                r"\b(distract(ed)?|can't\s+focus|cannot\s+focus|poor\s+concentration|concentration\s+issues)\b",
                r"\b(mentally\s+foggy|brain\s+fog)\b",
            ],
            "sadness": [
                r"\b(sad|depressed|depression|down|low\s+mood|hopeless)\b",
                r"\b(crying|tearful)\b",
            ],
        }

        # duration regex: supports phrases like "for 2 weeks", "for three days", "since last month"
        self._duration_patterns = [
            # numeric days/weeks/months
            (r"for\s+(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>day|days|week|weeks|month|months|year|years)\b", True),
            (r"since\s+(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>day|days|week|weeks|month|months|year|years)\b", True),
            # textual small set (days/weeks/months)
            (r"for\s+two\s+(?P<unit>days|weeks|months)\b", False),
            (r"for\s+three\s+(?P<unit>days|weeks|months)\b", False),
            (r"for\s+four\s+(?P<unit>days|weeks|months)\b", False),
            (r"for\s+more\s+than\s+(?P<num>\d+)\s*(?P<unit>days|weeks)\b", True),
        ]

        self._unit_to_days = {
            "day": 1,
            "days": 1,
            "week": 7,
            "weeks": 7,
            "month": 30,
            "months": 30,
            "year": 365,
            "years": 365,
        }

    def extract(self, text: str) -> SymptomExtraction:
        q = (text or "").lower()

        symptoms: Dict[str, float] = {}
        matched_signals: Dict[str, str] = {}

        # symptom patterns
        for symptom_key, patterns in self._patterns.items():
            for pat in patterns:
                if re.search(pat, q):
                    # intensity heuristic: presence=1.0
                    symptoms[symptom_key] = 1.0
                    matched_signals[symptom_key] = pat
                    break

        # duration extraction
        duration_days = self._extract_duration_days(q)

        # Map sadness to your requested key name "sadness"
        # Internal keys already match requested list except "sleep issues" etc.
        return SymptomExtraction(symptoms=symptoms, duration_days=duration_days, matched_signals=matched_signals)

    def _extract_duration_days(self, q: str) -> Optional[float]:
        # 1) numeric capture
        for pat, numeric in self._duration_patterns:
            m = re.search(pat, q)
            if not m:
                continue

            unit = m.groupdict().get("unit")
            if not unit:
                continue

            unit = unit.lower()

            if numeric:
                num_raw = m.groupdict().get("num")
                if num_raw is None:
                    continue
                try:
                    num = float(num_raw)
                except ValueError:
                    continue
                days = num * self._unit_to_days.get(unit, 0)
                if days > 0:
                    return float(days)

            # textual fallback for two/three/four variants
            # If pattern matched with unit only, infer num from the prefix phrase.
            # We detect that by checking the exact matched string.
            matched = m.group(0)
            if matched.startswith("for two"):
                num = 2
            elif matched.startswith("for three"):
                num = 3
            elif matched.startswith("for four"):
                num = 4
            else:
                num = 1

            days = num * self._unit_to_days.get(unit, 0)
            if days > 0:
                return float(days)

        # 2) common clinical shorthand: "x+ weeks" not captured above
        m = re.search(r"(?P<num>\d+)\s*(?P<unit>weeks|week|months|month)\b", q)
        if m:
            num = float(m.group("num"))
            unit = m.group("unit").lower()
            days = num * self._unit_to_days.get(unit, 0)
            if days > 0:
                return float(days)

        return None

