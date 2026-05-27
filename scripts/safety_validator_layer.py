"""Deterministic Safety Validator Layer

Purpose:
- Deterministically validate the composed response before returning it.
- Enforce: no unsafe advice, no hallucinated diagnosis, no dangerous claims.
- Ensure crisis escalation is present when needed.

This layer is intentionally LLM-free.

How it works (high level):
1) Detect crisis/risk triggers from the incoming cognitive output.
2) Validate that crisis flows contain mandatory resource guidance.
3) Detect dangerous medical-claim patterns and redact/replace with safe language.
4) Return a final, validated response.

Integrate by calling:
    validator = SafetyValidatorLayer()
    safe_text = validator.validate(user_query, cognitive_output, response_text)

"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class SafetyValidationResult:
    response: str
    adjusted: bool


class SafetyValidatorLayer:
    """Deterministic validation for clinical safety enforcement."""

    # Crisis resources (kept short, deterministic)
    INDIA_RESOURCES = (
        "🇮🇳 India: AASRA +91-22-27546669; iCall +91-9152987821; Crisis Line 1-800-110-7000 (24/7)."
    )
    US_RESOURCES = "🇺🇸 US: Call or text 988 (Lifeline)."
    UK_RESOURCES = "🇬🇧 UK: Samaritans 116 123."

    def __init__(self):
        # Medical claim patterns that are risky if hallucinated.
        self._diagnosis_claim_patterns = [
            r"\b(you have|you are suffering from|diagnosed with)\b",
            r"\b(bipolar|schizophrenia|ptsd|depression|anxiety)\b\s*(?:disorder|diagnosis)",
        ]
        self._dangerous_action_patterns = [
            r"\b(dosage|mg|take|medication)\b",
            r"\b(try to kill|suicide method|how to)\b",
        ]

        # Ensure crisis guidance presence (any of these tokens)
        self._crisis_guidance_tokens = [
            "988",
            "Samaritans",
            "AASRA",
            "iCall",
            "Crisis Line",
            "116 123",
            "helpline",
            "emergency services",
        ]

    def validate(self, user_query: str, cognitive_output: object, response_text: str) -> SafetyValidationResult:
        """Validate and adjust response_text if needed."""

        adjusted = False

        risk_level = getattr(cognitive_output, "risk_level", None)
        flow_id = getattr(cognitive_output, "flow_id", None)

        crisis_needed = (risk_level == "high") or (flow_id == "crisis_emergency")

        # 1) If crisis is needed, force crisis escalation template if missing.
        if crisis_needed:
            if not self._contains_any(response_text, self._crisis_guidance_tokens):
                response_text = self._force_crisis_response(user_query)
                adjusted = True
            return SafetyValidationResult(response=response_text, adjusted=adjusted)

        # 2) Non-crisis: strip hallucinated diagnosis/dangerous medical claims.
        if self._contains_any_regex(response_text, self._diagnosis_claim_patterns):
            response_text = self._redact_diagnosis(response_text)
            adjusted = True

        if self._contains_any_regex(response_text, self._dangerous_action_patterns):
            response_text = self._redact_medication_or_methods(response_text)
            adjusted = True

        # 3) Ensure safe educational framing.
        # If response contains explicit diagnosis claims, it is already redacted.
        return SafetyValidationResult(response=response_text, adjusted=adjusted)

    def _contains_any(self, text: str, tokens) -> bool:
        t = (text or "").lower()
        for tok in tokens:
            if tok.lower() in t:
                return True
        return False

    def _contains_any_regex(self, text: str, patterns) -> bool:
        for p in patterns:
            if re.search(p, text or "", flags=re.IGNORECASE):
                return True
        return False

    def _force_crisis_response(self, user_query: str) -> str:
        # Deterministic escalation template.
        return (
            "I’m really concerned about what you’re sharing. Your safety comes first.\n\n"
            "Please reach out to immediate help now: \n"
            f"{self.INDIA_RESOURCES}\n"
            f"{self.US_RESOURCES}\n"
            f"{self.UK_RESOURCES}\n\n"
            "If you’re in immediate danger, contact your local emergency services right now."
        )

    def _redact_diagnosis(self, text: str) -> str:
        # Replace direct diagnosis framing with safe educational language.
        text = re.sub(
            r"\b(you have|you are suffering from|diagnosed with)\b.*?\.$",
            "I can’t diagnose you. What you describe may be related to stress or mental health challenges, and it would be best to talk with a qualified professional.",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        # Also hard-remove the most risky diagnosis-like phrases.
        text = re.sub(
            r"\b(bipolar|schizophrenia|ptsd|depression|anxiety)\b\s*(?:disorder|diagnosis)",
            "mental health concerns",
            text,
            flags=re.IGNORECASE,
        )
        return text

    def _redact_medication_or_methods(self, text: str) -> str:
        return (
            "I can’t provide medication instructions or methods. If you’re feeling unsafe or overwhelmed, please contact a qualified medical/mental health professional or a local crisis helpline immediately."
        )

