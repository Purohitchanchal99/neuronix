"""Local Emotion Detector (LLM-free)

Detects:
- anxious
- hopeless
- panic
- calm
- stressed
- suicidal-risk

This replaces keyword-only logic scattered across the repo.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class EmotionDetection:
    label: str
    intensity: float
    matched_rule: Optional[str] = None


class LocalEmotionDetector:
    """Deterministic emotion detector using lightweight pattern rules.

    Notes:
    - This is intentionally not a trainable ML model yet.
    - Designed to be a drop-in replacement for earlier keyword heuristics.
    """

    # Primary labels requested by you
    LABEL_ANXIOUS = "anxious"
    LABEL_HOPELESS = "hopeless"
    LABEL_PANIC = "panic"
    LABEL_CALM = "calm"
    LABEL_STRESSED = "stressed"
    LABEL_SUICIDAL = "suicidal-risk"

    def __init__(self):
        # order matters: suicidal/panic first
        self._rules: Tuple[Tuple[str, str, float], ...] = (
            # suicidal-risk
            ("suicidal", "suicide|k(ill)?\s+my\s+self|i\s+want\s+to\s+die|end\s+my\s+life|hurt\s+myself|harm\s+myself|\bsui(cide|cidal)\b", 1.0),
            ("panic", "panic|gabrahat|ghabrana|can't\s+breathe|can't\s+breath|hypervent|heart\s+pounding|immediately\s+danger", 0.9),
            # hopeless
            ("hopeless", "hopeless|worthless|nothing\s+matters|no\s+one\s+cares|\bempty\b|\bno\s+hope\b|can't\s+go\s+on", 0.85),
            # anxious
            ("anxious", "anxious|anxiety|worried|worry|overthinking|can't\s+stop\s+thinking|restless|nervous", 0.8),
            # stressed
            ("stressed", "stressed|stress|overwhelmed|tension|burnt\s*out|burnout|pressure|irritable", 0.75),
            # calm fallback handled separately
        )

    def detect(self, text: str) -> EmotionDetection:
        q = (text or "").lower()

        import re

        for rule_name, pattern, intensity in self._rules:
            if re.search(pattern, q):
                # map rule_name to requested labels
                if rule_name == "suicidal":
                    label = self.LABEL_SUICIDAL
                elif rule_name == "panic":
                    label = self.LABEL_PANIC
                elif rule_name == "hopeless":
                    label = self.LABEL_HOPELESS
                elif rule_name == "anxious":
                    label = self.LABEL_ANXIOUS
                elif rule_name == "stressed":
                    label = self.LABEL_STRESSED
                else:
                    label = rule_name

                return EmotionDetection(label=label, intensity=float(intensity), matched_rule=rule_name)

        # calm / low arousal default
        return EmotionDetection(label=self.LABEL_CALM, intensity=0.2, matched_rule=None)

