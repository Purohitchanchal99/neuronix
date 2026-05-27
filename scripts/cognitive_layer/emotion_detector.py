"""Emotion detector for Cognitive Layer v1 (LLM-free).

STEP 3 — Build Emotion Detector
Detect:
- anxious
- hopeless
- panic
- calm
- stressed
- suicidal-risk

Implements a deterministic local detector and exposes the wrapper
class expected by `scripts/cognitive_layer/cognitive_layer_v1.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from scripts.emotion_detector import LocalEmotionDetector


@dataclass
class EmotionPrediction:
    label: str
    intensity: float


class DistressEmotionDetector:
    """Wrapper used by Cognitive Layer v1."""

    def __init__(self):
        self._detector = LocalEmotionDetector()

    def predict(self, text: str) -> EmotionPrediction:
        det = self._detector.detect(text)
        return EmotionPrediction(label=det.label, intensity=det.intensity)

