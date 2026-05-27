"""Symbolic reasoning engine for Cognitive Layer v1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ReasoningOutput:
    flow_id: str
    risk_level: str
    condition_guess: Optional[str]
    safety_notes: List[str]


class ReasoningEngine:
    def __init__(self):
        # minimal rules for now
        pass

    def reason(
        self,
        intent: str,
        emotion_label: str,
        symptoms: Dict[str, float],
        duration_days: Optional[float],
    ) -> ReasoningOutput:
        # crisis
        if intent == "crisis" or emotion_label == "suicidal-risk":
            return ReasoningOutput(
                flow_id="crisis_emergency",
                risk_level="high",
                condition_guess=None,
                safety_notes=["Immediate helpline guidance required."],
            )

        # distress risk
        risk_level = "low"
        if emotion_label in {"hopeless", "panic", "suicidal-risk"}:
            risk_level = "high"
        elif emotion_label in {"stressed", "anxious"}:
            risk_level = "medium"

        # depression education flow heuristic
        low_mood = symptoms.get("low_mood", 0.0) > 0
        sleep_issue = symptoms.get("sleep_issue", 0.0) > 0
        fatigue = symptoms.get("fatigue", 0.0) > 0

        if low_mood and (duration_days is None or duration_days >= 14) and (sleep_issue or fatigue):
            return ReasoningOutput(
                flow_id="depression_education_flow",
                risk_level=risk_level if risk_level != "low" else "medium",
                condition_guess="depression",
                safety_notes=[],
            )

        # anxiety flow heuristic
        anxious_like = emotion_label in {"anxious", "panic"} or symptoms.get("concentration", 0) > 0
        if anxious_like and sleep_issue:
            return ReasoningOutput(
                flow_id="anxiety_education_flow",
                risk_level=risk_level if risk_level != "low" else "medium",
                condition_guess="anxiety",
                safety_notes=[],
            )

        # default mental health flow
        if intent in {"mental_health", "general"}:
            return ReasoningOutput(
                flow_id="general_mental_health_flow",
                risk_level=risk_level,
                condition_guess=None,
                safety_notes=[],
            )

        # learning flow
        if intent == "learning":
            return ReasoningOutput(
                flow_id="learning_flow",
                risk_level="low",
                condition_guess=None,
                safety_notes=[],
            )

        return ReasoningOutput(
            flow_id="unknown_flow",
            risk_level="low",
            condition_guess=None,
            safety_notes=[],
        )

