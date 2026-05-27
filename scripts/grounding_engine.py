"""Deterministic Grounding Engine

Goal:
- Convert retrieved knowledge chunks into structured clinical facts
- Never call external LLMs
- Provide grounded_facts to the response planner

This module is intentionally conservative and uses regex + heuristics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class ClinicalFacts:
    """Structured facts extracted from retrieved docs."""

    condition: str = ""
    definition: str = ""
    symptoms: List[str] = field(default_factory=list)
    criteria: List[str] = field(default_factory=list)
    coping_steps: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    followups: List[str] = field(default_factory=list)
    source_chunks: List[str] = field(default_factory=list)


class GroundingEngine:
    """Convert raw retrieved text into grounded clinical facts."""

    # Symptom-ish patterns
    _BULLET_SPLIT_RE = re.compile(r"(?:\n+|;|•|\u2022|\d+[\).]|-\s+)")

    # Common phrase starters
    _DEFINITION_STARTERS = [
        "is a",
        "refers to",
        "is characterized by",
        "is defined as",
        "consists of",
        "major depressive disorder",
        "depression",
    ]

    _SYMPTOM_PHRASES = [
        "symptoms include",
        "common symptoms",
        "include",
        "symptom",
        "criteria include",
        "core symptoms",
    ]

    _CRITERIA_HINTS = [
        "criteria",
        "dsm-5",
        "dsm",
        "icd-11",
        "icd",
        "threshold",
    ]

    _WARNING_PATTERNS = [
        "suicidal",
        "self-harm",
        "harm",
        "emergency",
        "crisis",
        "risk",
    ]

    _COPING_HINTS = [
        "coping",
        "self-care",
        "grounding",
        "breathing",
        "exercise",
        "sleep",
        "routine",
        "journal",
        "behavioral",
        "cbt",
        "dbt",
    ]

    def ground(self, query: str, retrieved_docs: Any, *, intent: Optional[str] = None, symptoms: Optional[Dict[str, float]] = None) -> ClinicalFacts:
        """Ground retrieved docs into structured facts.


        Args:
            query: user query text
            retrieved_docs: either a string (concatenated chunks) or list of docs
            intent: optional predicted intent
            symptoms: optional extracted symptom scores (from local extractor)
        """

        text = self._normalize_docs(retrieved_docs)
        facts = ClinicalFacts()

        # Condition guess from query
        facts.condition = self._infer_condition_from_query(query)

        # Capture some provenance
        facts.source_chunks = self._extract_source_snippets(retrieved_docs, max_chunks=3)

        # Definition: first few sentences that look like definition
        facts.definition = self._extract_definition(text, fallback=facts.definition)

        # Symptoms / criteria extraction
        facts.symptoms = self._extract_symptoms(text)
        facts.criteria = self._extract_criteria(text)

        # Coping / warnings / followups (heuristic)
        facts.coping_steps = self._extract_coping_steps(text)
        facts.warnings = self._extract_warnings(text)
        facts.followups = self._extract_followups(query, facts.condition, facts.symptoms)

        # Deterministic cleanup
        facts.symptoms = self._dedupe_preserve_order([self._clean_fact(s) for s in facts.symptoms if s.strip()])
        facts.criteria = self._dedupe_preserve_order([self._clean_fact(s) for s in facts.criteria if s.strip()])
        facts.coping_steps = self._dedupe_preserve_order([self._clean_fact(s) for s in facts.coping_steps if s.strip()])
        facts.warnings = self._dedupe_preserve_order([self._clean_fact(s) for s in facts.warnings if s.strip()])
        facts.followups = self._dedupe_preserve_order([self._clean_fact(s) for s in facts.followups if s.strip()])

        # Fallbacks if extraction yields nothing
        if not facts.symptoms and symptoms:
            facts.symptoms = [k.replace("_", " ") for k, v in symptoms.items() if v and v > 0]

        return facts

    def ground_with_confidence(
        self,
        query: str,
        retrieved_docs: Any,
        *,
        intent: Optional[str] = None,
        symptoms: Optional[Dict[str, float]] = None,
    ) -> tuple[ClinicalFacts, float]:
        """Ground + compute deterministic grounding confidence.

        grounding_confidence = non_empty_ratio over:
        definition, symptoms, criteria, coping_steps, warnings, followups
        """
        facts = self.ground(
            query,
            retrieved_docs,
            intent=intent,
            symptoms=symptoms,
        )

        fields = [
            facts.definition,
            facts.symptoms,
            facts.criteria,
            facts.coping_steps,
            facts.warnings,
            facts.followups,
        ]

        total_fields = len(fields)
        if total_fields == 0:
            return facts, 0.0

        non_empty = 0
        for f in fields:
            if isinstance(f, str):
                if f.strip():
                    non_empty += 1
            else:
                if f:
                    non_empty += 1

        grounding_confidence = non_empty / float(total_fields)
        return facts, float(grounding_confidence)


    def _normalize_docs(self, retrieved_docs: Any) -> str:
        if retrieved_docs is None:
            return ""
        if isinstance(retrieved_docs, str):
            return retrieved_docs

        # list/iterable of docs or dicts
        parts: List[str] = []
        try:
            iterable: Iterable[Any] = retrieved_docs  # type: ignore
        except Exception:
            return str(retrieved_docs)

        for d in iterable:
            if d is None:
                continue
            content = getattr(d, "page_content", None) or getattr(d, "content", None)
            if content:
                parts.append(str(content))
            else:
                parts.append(str(d))
        return "\n\n".join(parts)

    def _extract_source_snippets(self, retrieved_docs: Any, *, max_chunks: int = 3) -> List[str]:
        if retrieved_docs is None:
            return []
        if isinstance(retrieved_docs, str):
            return []
        out: List[str] = []
        try:
            iterable: Iterable[Any] = retrieved_docs  # type: ignore
        except Exception:
            return []
        for d in iterable:
            if d is None:
                continue
            content = getattr(d, "page_content", None) or getattr(d, "content", None)
            if not content:
                continue
            out.append(str(content)[:220].strip())
            if len(out) >= max_chunks:
                break
        return out

    def _infer_condition_from_query(self, query: str) -> str:
        q = (query or "").lower()
        # common conditions
        for cond in [
            "depression",
            "anxiety",
            "ocd",
            "panic",
            "ptsd",
            "bipolar",
            "adhd",
        ]:
            if cond in q:
                return cond
        return ""

    def _extract_definition(self, text: str, *, fallback: str = "") -> str:
        t = text.strip()
        if not t:
            return fallback

        # Sentence split (light)
        sentences = re.split(r"(?<=[.!?])\s+", t)
        for s in sentences[:8]:
            s_norm = s.lower()
            if any(st in s_norm for st in ["is a", "is defined", "refers to", "is characterized"]):
                return s.strip()

        # Keyword fallback: take line that mentions definition-ish starters
        for line in t.splitlines()[:120]:
            ln = line.strip()
            if not ln:
                continue
            lnl = ln.lower()
            if any(x in lnl for x in ["depression is", "anxiety is", "defined as", "refers to"]):
                return ln

        return fallback

    def _extract_symptoms(self, text: str) -> List[str]:
        if not text:
            return []

        lower = text.lower()
        # Try to find a region after a symptoms phrase
        candidates: List[str] = []

        symptom_headers = [
            "symptoms include",
            "common symptoms",
            "symptoms are",
            "core symptoms",
            "include",
        ]

        # Extract segments around headers
        for header in symptom_headers:
            idx = lower.find(header)
            if idx == -1:
                continue
            segment = text[idx : idx + 900]
            candidates.extend(self._extract_bullets_from_segment(segment))

        # If nothing found, use generic bullet extraction
        if not candidates:
            candidates.extend(self._extract_bullets_from_segment(text[:1400]))

        # Filter: keep phrases that look like symptoms (short, not too narrative)
        out: List[str] = []
        for c in candidates:
            s = self._clean_fact(c)
            if not s:
                continue
            sl = s.lower()
            # remove obviously non-symptoms
            if any(bad in sl for bad in ["dsm", "icd", "criteria", "disclaimer", "resource", "treatment"]):
                continue
            # too long -> split
            if len(s) > 90:
                # attempt sub-split by commas
                for part in [p.strip() for p in s.split(",") if p.strip()]:
                    if 2 <= len(part) <= 70:
                        out.append(part)
                continue
            if len(s) >= 3:
                out.append(s)

        # extra: if we can identify symptom list like "fatigue" etc, keep as is
        return out

    def _extract_criteria(self, text: str) -> List[str]:
        if not text:
            return []
        lower = text.lower()

        # Look for criteria regions
        if any(h in lower for h in self._CRITERIA_HINTS):
            # heuristic: return bullet-like items within first 1200 chars
            seg = text[:1400]
            return self._extract_bullets_from_segment(seg, prefer_numbered=True)
        return []

    def _extract_coping_steps(self, text: str) -> List[str]:
        if not text:
            return []
        lower = text.lower()
        if not any(h in lower for h in self._COPING_HINTS):
            return []

        seg = text[:1800]
        candidates = self._extract_bullets_from_segment(seg)
        # filter to coping-ish phrases
        out: List[str] = []
        for c in candidates:
            s = self._clean_fact(c)
            sl = s.lower()
            if not s:
                continue
            if any(h in sl for h in ["ground", "breath", "sleep", "routine", "exercise", "talk", "journ", "write", "walk", "meditat", "cbt", "dbt"]):
                out.append(s)
        return out

    def _extract_warnings(self, text: str) -> List[str]:
        if not text:
            return []
        lower = text.lower()
        if not any(p in lower for p in self._WARNING_PATTERNS):
            return []

        seg = text[:1800]
        candidates = self._extract_bullets_from_segment(seg)

        out: List[str] = []
        for c in candidates:
            s = self._clean_fact(c)
            sl = s.lower()
            if any(p in sl for p in self._WARNING_PATTERNS):
                out.append(s)

        # If we have no bullet extraction but text includes crisis wording, add generic warning
        if not out and any(p in lower for p in ["suicidal", "self-harm", "crisis", "emergency"]):
            out.append("If you feel in immediate danger or have thoughts of self-harm, seek urgent help right now.")

        return out

    def _extract_followups(self, query: str, condition: str, symptoms: List[str]) -> List[str]:
        q = (query or "").strip()
        if not q:
            return ["Kab se ho raha hai?"]

        # Prefer Hindi followups to match template tone used elsewhere
        base: List[str] = []

        if condition:
            base.append(f"{condition.title()} ke liye aapko ye symptoms kab se feel ho rahe hain?")
        else:
            base.append("Ye problem kab se start hui?")

        # duration / severity
        base.append("Din bhar mein kitni frequency/intensity rehti hai (low/medium/high)?")

        # symptom-level followup
        if symptoms:
            s0 = symptoms[0]
            base.append(f"{s0} kitna zyada affect kar raha hai—sleep, appetite, ya daily routine?")

        # Keep concise
        return base[:3]

    def _extract_bullets_from_segment(self, segment: str, *, prefer_numbered: bool = False) -> List[str]:
        if not segment:
            return []

        # Normalize to lines
        lines = [ln.strip() for ln in segment.splitlines() if ln.strip()]

        # If prefer numbered, prioritize lines starting with digits
        selected: List[str] = []
        if prefer_numbered:
            for ln in lines:
                if re.match(r"^\s*(\d+|\d+[\).])\s+", ln):
                    selected.append(ln)
            if selected:
                return [re.sub(r"^\s*(\d+[\).])\s*", "", s).strip() for s in selected][:15]

        # Otherwise, take anything bullet-ish
        for ln in lines[:120]:
            # remove leading bullets
            cleaned = re.sub(r"^(?:[-•\u2022]|\d+[\).])\s*", "", ln).strip()
            if not cleaned:
                continue
            # Keep shortish items
            if 3 <= len(cleaned) <= 110:
                selected.append(cleaned)

        # If no selected, attempt splitting by separators
        if not selected:
            parts = [p.strip() for p in re.split(self._BULLET_SPLIT_RE, segment) if p and p.strip()]
            selected = [p for p in parts if 3 <= len(p) <= 90][:25]

        return selected[:25]

    def _clean_fact(self, s: str) -> str:
        s = re.sub(r"\s+", " ", (s or "")).strip()
        # Remove trailing punctuation that looks like full sentence ends
        s = s.strip(" -–—\t")
        return s

    def _dedupe_preserve_order(self, items: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for x in items:
            k = x.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(x)
        return out

