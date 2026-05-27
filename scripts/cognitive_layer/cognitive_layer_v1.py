"""NEURONIX Cognitive Layer v1 runtime (LLM-free)."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Dict, Optional, Tuple, List

from .config import llm_enabled

# NOTE: This module is intentionally LLM-free.
# We fail fast at runtime if NEURONIX_LLM_ENABLED is accidentally set to true.


from .intent_classifier import LocalIntentClassifier
from .emotion_detector import DistressEmotionDetector
from .symptom_extractor import SymptomExtractor
from .reasoning_engine import ReasoningEngine
from .response_planner import ResponsePlanner
from .template_composer import TemplateComposer
from scripts.grounding_engine import GroundingEngine



@dataclass
class CognitiveOutput:
    response: str
    risk_level: str
    intent: str
    flow_id: str
    condition_guess: Optional[str] = None


class CognitiveLayerV1:
    def __init__(self, vector_store=None):
        # Fail fast if external LLMs are enabled.
        # This ensures NEURONIX_LLM_ENABLED gates Gemini/OpenAI/LiteLLM usage.
        if llm_enabled():
            raise RuntimeError(
                "NEURONIX_LLM_ENABLED=true: Cognitive Layer v1 must run LLM-free. "
                "Set NEURONIX_LLM_ENABLED=false."
            )

        self.vector_store = vector_store

        self.intent_classifier = LocalIntentClassifier()
        self.emotion_detector = DistressEmotionDetector()
        self.symptom_extractor = SymptomExtractor()
        self.reasoning = ReasoningEngine()
        self.planner = ResponsePlanner()
        self.composer = TemplateComposer()

    def retrieve(self, query: str, k: int = 4) -> str:
        if self.vector_store is None:
            return ""
        if hasattr(self.vector_store, "similarity_search"):
            docs = self.vector_store.similarity_search(query, k=k)
            if not docs:
                return ""
            # deterministic concatenation
            return "\n\n".join([d.page_content[:450] for d in docs])
        return ""

    def run(self, user_query: str) -> CognitiveOutput:
        if llm_enabled():
            raise RuntimeError("LLM calls are disabled for Cognitive Layer v1. Set NEURONIX_LLM_ENABLED=false.")

        # LLM-free cognitive components assume a deterministic reasoning output.



        intent_pred = self.intent_classifier.predict(user_query)
        emotion_pred = self.emotion_detector.predict(user_query)
        symptoms = self.symptom_extractor.extract(user_query)

        reasoning_out = self.reasoning.reason(
            intent=intent_pred.intent,
            emotion_label=emotion_pred.label,
            symptoms=symptoms.symptoms,
            duration_days=symptoms.duration_days,
        )

        # retrieval grounding (always local, routed through RetrievalAdapter)
        from scripts.retrieval_adapter import RetrievalAdapter

        adapter = RetrievalAdapter(self.vector_store, default_k=4)
        retrieved_context = adapter.retrieve_grounding(user_query, k=4)

        # Ground retrieved knowledge into structured clinical facts
        grounding = GroundingEngine()
        grounded_facts = grounding.ground(
            user_query,
            retrieved_context,
            intent=intent_pred.intent,
            symptoms=symptoms.symptoms if hasattr(symptoms, "symptoms") else None,
        )

        # Unknown-term learning loop (deterministic, LLM-free)
        # Store when retrieval/grounding is weak.
        from scripts.unknown_terms_store import UnknownTermsStore, UnknownTermEvent
        unknown_store = UnknownTermsStore()

        # Heuristic confidence signals
        retrieval_confidence = 1.0 if retrieved_context else 0.0
        grounding_empty = (
            not grounded_facts.symptoms
            and not grounded_facts.definition
            and not grounded_facts.criteria
            and not grounded_facts.coping_steps
            and not grounded_facts.warnings
        )

        # Ontology mapping strength proxy (kept for backward compatibility); not required for learning loop.
        # Note: reasoning_out may not expose an `intent` attribute.
        _ontology_similarity_weak = bool(reasoning_out.condition_guess) is False


        if grounding_empty or retrieved_context == "" or retrieval_confidence < 0.5:
            unknown_store.append(
                UnknownTermEvent(
                    query=user_query,
                    normalized=user_query.strip(),
                    top_match=None,
                    score=float(retrieval_confidence),
                    timestamp=time.time(),
                )
            )

        # Planner must be facts-first: keep raw retrieval only as debug.
        retrieved_context = ""


        planned = self.planner.plan(
            flow_id=reasoning_out.flow_id,
            condition_guess=reasoning_out.condition_guess,
            retrieved_context=retrieved_context,
            risk_level=reasoning_out.risk_level,
            grounded_facts={
                "condition": grounded_facts.condition,
                "definition": grounded_facts.definition,
                "symptoms": grounded_facts.symptoms,
                "criteria": grounded_facts.criteria,
                "coping_steps": grounded_facts.coping_steps,
                "warnings": grounded_facts.warnings,
                "followups": grounded_facts.followups,
            },
        )


        response = self.composer.compose(planned)

        return CognitiveOutput(
            response=response,
            risk_level=reasoning_out.risk_level,
            intent=intent_pred.intent,
            flow_id=reasoning_out.flow_id,
            condition_guess=reasoning_out.condition_guess,
        )

