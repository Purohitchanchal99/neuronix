"""Response planner for Cognitive Layer v1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class PlannedResponse:
    sections: List[str]
    follow_up_question: Optional[str]
    safety_note: Optional[str]


class ResponsePlanner:
    def plan(
        self,
        flow_id: str,
        condition_guess: Optional[str],
        retrieved_context: str,
        risk_level: str,
        grounded_facts: Optional[dict] = None,
    ) -> PlannedResponse:
        """Plan a deterministic response.

        IMPORTANT: when `grounded_facts` is provided, this planner should use it
        and avoid echoing raw chunks directly.
        """

        sections: List[str] = []

        if flow_id == "crisis_emergency":
            return PlannedResponse(
                sections=[],
                follow_up_question=None,
                safety_note=(
                    "Bhai, ye serious lag raha hai. Please help immediately: talk to a trusted person or contact local helplines." \
                    " Your safety comes first."
                ),
            )

        # grounding section
        if retrieved_context:
            sections.append(f"Grounding (from your knowledge base):\n{retrieved_context[:900]}")

        # educational section
        if flow_id == "depression_education_flow":
            sections.append(
                "Educational overview (depression):\n- Low mood and interest loss are common.\n- If symptoms persist 2+ weeks, professional assessment helps."
            )
            follow_up = "Aapko ye low mood/symptoms kab se ho rahe hain (days/weeks)?"
            return PlannedResponse(sections=sections, follow_up_question=follow_up, safety_note=None)

        if flow_id == "anxiety_education_flow":
            sections.append(
                "Educational overview (anxiety):\n- Excess worry can feel physical and tiring.\n- Step-by-step coping and professional support can help."
            )
            follow_up = "Kya ye anxiety constant rehti hai ya specific situations mein badhti hai?"
            return PlannedResponse(sections=sections, follow_up_question=follow_up, safety_note=None)

        # default
        sections.append("Coping suggestions:\n- Take one small step today.\n- Sleep/rest and talk to someone you trust.")
        follow_up = "Aap thoda detail bataoge—stress, sleep, ya mood mein se kis cheez ka zyada issue hai?"
        return PlannedResponse(
            sections=sections,
            follow_up_question=follow_up,
            safety_note="Educational info only. If symptoms feel severe or worsening, please consult a professional.",
        )

