"""Local Intent Classifier (LLM-free placeholder)

Creates a simple deterministic classifier.

Target intents:
- depression
- anxiety
- stress
- crisis
- educational
- greeting
- followup
- recommendation
- unknown

This module is intentionally lightweight; you can later replace the internals
with DistilBERT / TinyBERT / MiniLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class IntentPrediction:
    intent: str
    confidence: float


class LocalIntentClassifier:
    def __init__(self):
        pass

    def predict(self, text: str) -> IntentPrediction:
        q = (text or "").lower()

        # crisis
        if any(p in q for p in [
            "i want to die",
            "i can't take it anymore",
            "suicidal",
            "kill myself",
            "hurt myself",
            "harm myself",
            "end my life",
        ]):
            return IntentPrediction("crisis", 0.98)

        # greeting
        if any(w in q for w in ["hi ", "hello", "namaste", "how are you"]):
            return IntentPrediction("greeting", 0.9)

        # follow-up markers
        if any(w in q for w in ["more", "again", "still have questions", "follow up", "next"]):
            return IntentPrediction("followup", 0.75)

        # recommendation request
        if any(w in q for w in ["recommend", "should i", "what can i do", "suggest", "help me with"]):
            return IntentPrediction("recommendation", 0.7)

        # educational
        if any(w in q for w in ["teach", "explain", "what is", "how to", "learn", "course", "python", "recursion"]):
            return IntentPrediction("educational", 0.8)

        # anxiety
        if any(w in q for w in ["anxious", "anxiety", "worried", "panic", "overthinking", "can't breathe"]):
            return IntentPrediction("anxiety", 0.75)

        # stress
        if any(w in q for w in ["stressed", "stress", "overwhelmed", "burnout", "pressure", "tension", "irritable"]):
            return IntentPrediction("stress", 0.7)

        # depression
        if any(w in q for w in ["depressed", "depression", "sad", "hopeless", "low mood"]):
            return IntentPrediction("depression", 0.7)

        return IntentPrediction("unknown", 0.3)

