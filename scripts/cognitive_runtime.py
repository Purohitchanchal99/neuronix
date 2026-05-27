"""Neuronix Cognitive Runtime (orchestration entrypoint)

This provides ONE unified, deterministic execution pipeline that stitches together:
- intent classification (local)
- emotion detection (local)
- symptom extraction (local)
- symbolic reasoning (decision-making)
- retrieval grounding (local)
- response planning (structured blocks)
- template composition (final deterministic response)

No external LLM calls are allowed in Cognitive Layer v1 mode.

Usage:
    runtime = NeuronixCognitiveRuntime(vector_store=my_chroma_or_none)
    out = runtime.run("I feel hopeless...")

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from scripts.cognitive_layer.config import llm_enabled
from scripts.cognitive_layer.cognitive_layer_v1 import CognitiveLayerV1
from scripts.safety_validator_layer import SafetyValidatorLayer
from scripts.conversation_state import conversation_state_store



@dataclass
class CognitiveRuntimeOutput:

    response: str
    risk_level: str
    intent: str
    flow_id: str
    condition_guess: Optional[str] = None
    retrieved_context_used: bool = False


class NeuronixCognitiveRuntime:
    """Unified orchestration entrypoint for Cognitive Layer v1."""

    def __init__(self, vector_store: Any = None):
        if llm_enabled():
            # Hard fail to prevent accidental external LLM calls.
            raise RuntimeError(
                "NEURONIX_LLM_ENABLED=true: Cognitive runtime must run LLM-free. Set NEURONIX_LLM_ENABLED=false."
            )

        self.cognitive = CognitiveLayerV1(vector_store=vector_store)
        self.vector_store = vector_store
        self.validator = SafetyValidatorLayer()


    def run(self, user_query: str, *, k: int = 4) -> CognitiveRuntimeOutput:
        # We keep k for future routing; current CognitiveLayerV1.retrieve uses default.
        # If needed, CognitiveLayerV1.retrieve can be extended to accept k.
        out = self.cognitive.run(user_query)
        validated = self.validator.validate(user_query, out, out.response)
        out.response = validated.response

        retrieved_context_used = bool(getattr(self.cognitive, "vector_store", None) is not None)

        # Update longitudinal conversation state (critical for mental-health systems)
        conversation_state_store.update_from_cognitive_output(
            "default",  # placeholder user_id hook (runtime currently has no user_id parameter)

            intent=out.intent,
            flow_id=out.flow_id,
            risk_level=out.risk_level,
            condition_guess=out.condition_guess,
            emotion_label=None,
            extracted_symptoms=None,
            follow_up_question=None,
            retrieved_context_used=retrieved_context_used,
        )




        return CognitiveRuntimeOutput(
            response=out.response,
            risk_level=out.risk_level,
            intent=out.intent,
            flow_id=out.flow_id,
            condition_guess=out.condition_guess,
            retrieved_context_used=retrieved_context_used,
        )


# Backwards-compatible alias (requested naming option)
NeuronixCognitiveRuntime = NeuronixCognitiveRuntime

