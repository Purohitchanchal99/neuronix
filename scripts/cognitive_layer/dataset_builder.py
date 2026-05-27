"""Starter dataset builder for local classifier fine-tuning.

We generate a small seed dataset from:
- existing keyword rules (scripts/intent_router.py)
- existing symptom keywords and crisis keywords (scripts/neuronix_core.py)

This is NOT intended to be clinical-grade; it's a bootstrapping dataset.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class LabeledExample:
    text: str
    label: str


def _normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def build_intent_dataset() -> List[LabeledExample]:
    """Build a bootstrapping intent dataset.

    Labels align to QueryIntent from scripts/intent_router.py.
    """
    # Import without triggering any LLM code.
    from scripts.intent_router import IntentRouter, QueryIntent

    router = IntentRouter()

    # Minimal templates (we'll rely on keyword hits)
    seeds: List[Tuple[str, QueryIntent]] = []

    # Crisis examples
    crisis_texts = [
        "I want to die",
        "I can't take it anymore",
        "Suicidal thoughts",
        "I want to kill myself",
        "hurt myself",
    ]
    for t in crisis_texts:
        seeds.append((t, QueryIntent.CRISIS))

    mental_texts = [
        "I feel anxious and worried",
        "I'm depressed and sad",
        "I can't sleep",
        "I'm stressed and overwhelmed",
        "I'm angry and irritated",
        "I feel hopeless",
        "I feel lonely and isolated",
        "I can't focus and have concentration issues",
    ]
    for t in mental_texts:
        seeds.append((t, QueryIntent.MENTAL_HEALTH))

    learning_texts = [
        "Teach me python loops",
        "What is a variable?",
        "How to write functions in python",
        "Explain recursion",
        "Learn coding debugging",
    ]
    for t in learning_texts:
        seeds.append((t, QueryIntent.LEARNING))

    general_texts = [
        "Hi how are you",
        "Hello",
        "What's up",
        "Namaste",
    ]
    for t in general_texts:
        seeds.append((t, QueryIntent.GENERAL))

    # Expand with simple paraphrases (cheap bootstrapping)
    paraphrases = [
        lambda x: x,
        lambda x: x + ".",
        lambda x: "I'm feeling " + x.lower(),
        lambda x: "Can you help me with " + x.lower() + "?",
    ]

    out: List[LabeledExample] = []
    for base, intent in seeds:
        for p in paraphrases:
            txt = _normalize_spaces(p(base))
            out.append(LabeledExample(text=txt, label=intent.value))

    # Ensure at least a few examples per class
    return out

