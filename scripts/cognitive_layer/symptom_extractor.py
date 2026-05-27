"""Symptom extractor for Cognitive Layer v1 (LLM-free).

STEP 4 — Build Symptom Extractor
Extract:
- sleep issues
- appetite changes
- fatigue
- concentration issues
- sadness
- duration

This replaces earlier keyword heuristics with the structured
extractor in `scripts/symptom_extractor.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from scripts.symptom_extractor import LocalSymptomExtractor


@dataclass
class SymptomExtraction:
    symptoms: Dict[str, float]
    duration_days: Optional[float] = None


class SymptomExtractor:
    def __init__(self):
        self._extractor = LocalSymptomExtractor()

    def extract(self, text: str) -> SymptomExtraction:
        out = self._extractor.extract(text)

        # cognitive_layer_v1/reasoning_engine expects keys:
        # sleep_issue, appetite_change, fatigue, concentration, low_mood
        symptoms: Dict[str, float] = {
            "sleep_issue": float(out.symptoms.get("sleep_issue", 0.0)),
            "appetite_change": float(out.symptoms.get("appetite_change", 0.0)),
            "fatigue": float(out.symptoms.get("fatigue", 0.0)),
            "concentration": float(out.symptoms.get("concentration", 0.0)),
            "low_mood": float(out.symptoms.get("sadness", 0.0)),
        }

        return SymptomExtraction(symptoms=symptoms, duration_days=out.duration_days)

