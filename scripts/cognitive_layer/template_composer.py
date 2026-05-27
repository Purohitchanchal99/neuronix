"""Deterministic template composer for Cognitive Layer v1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .response_planner import PlannedResponse


class TemplateComposer:
    def compose(self, planned: PlannedResponse) -> str:
        parts: List[str] = []

        # intro
        if planned.safety_note and planned.follow_up_question is None:
            parts.append("I’m really glad you shared this. I’m here with you.")
        else:
            parts.append("I hear you. Let’s take this step by step.")

        # sections
        for s in planned.sections:
            if s.strip():
                parts.append(s)

        # follow-up
        if planned.follow_up_question:
            parts.append(f"Follow-up: {planned.follow_up_question}")

        # safety note
        if planned.safety_note:
            parts.append(f"\nSafety: {planned.safety_note}")

        return "\n\n".join(parts).strip()

