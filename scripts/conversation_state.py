"""Conversation state for Neuronix Cognitive Runtime.

Critical: enable longitudinal reasoning by persisting user-relevant state
across calls.

This module is deterministic and LLM-free.

State fields requested:
- previous symptoms
- active concerns
- prior follow-ups
- emotional trend
- unresolved topics
- user coping history

Includes:
- In-memory store (deterministic update logic)
- SQLite-backed store with persistence + helper APIs:
  - summarize_state(user_id)
  - clear_state(user_id)
  - mark_follow_up_resolved(user_id, question)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

import json
import sqlite3
import threading
from pathlib import Path


def _now_utc() -> datetime:
    return datetime.utcnow()


def normalize_term(term: str) -> str:
    """Normalize symptom/concern tokens to reduce duplicates."""
    return (term or "").strip().lower()


_RISK_SCORE = {
    "critical": 3,
    "high": 2,
    "medium": 1,
    "low": -1,
}


@dataclass
class ConversationSnapshot:
    """Serializable snapshot of conversation state."""

    # (normalized_term, timestamp)
    previous_symptoms: List[Tuple[str, datetime]] = field(default_factory=list)

    # (normalized_term, timestamp)
    active_concerns: List[Tuple[str, datetime]] = field(default_factory=list)

    # Each dict: {"question": str, "resolved": bool, "timestamp": datetime}
    prior_follow_ups: List[Dict[str, Any]] = field(default_factory=list)

    # escalating | improving | stable
    emotional_trend: str = "stable"

    # Each dict: {"topic": str, "escalation_level": int, "timestamp": datetime}
    unresolved_topics: List[Dict[str, Any]] = field(default_factory=list)

    # Each dict: {"strategy": str, "context": str, "timestamp": datetime}
    coping_history: List[Dict[str, Any]] = field(default_factory=list)

    # Internal: rolling list of risk levels used for trend
    _recent_risk_levels: List[str] = field(default_factory=list)

    # Internal: track low-risk streak for auto-expiring unresolved topics
    _recent_low_turns: int = 0


class InMemoryConversationStateStore:
    """In-memory conversation state store with deterministic update logic."""

    def __init__(self):
        self._store: Dict[str, ConversationSnapshot] = {}

    def get(self, user_id: str) -> ConversationSnapshot:
        if user_id not in self._store:
            self._store[user_id] = ConversationSnapshot()
        return self._store[user_id]

    def update_from_cognitive_output(
        self,
        user_id: str,
        *,
        intent: str,
        flow_id: str,
        risk_level: str,
        condition_guess: Optional[str],
        emotion_label: Optional[str] = None,
        extracted_symptoms: Optional[List[str]] = None,
        follow_up_question: Optional[str] = None,
        retrieved_context_used: bool = False,
    ) -> ConversationSnapshot:
        """Update conversation state after each runtime call."""

        s = self.get(user_id)

        # Update recent risk levels for trend
        s._recent_risk_levels.append(risk_level)
        s._recent_risk_levels = s._recent_risk_levels[-6:]

        # Weighted scoring over rolling window
        total_score = 0
        for r in s._recent_risk_levels:
            total_score += _RISK_SCORE.get((r or "").lower(), 0)

        # Trend update thresholds
        if total_score >= 4:
            s.emotional_trend = "escalating"
        elif total_score <= -3:
            s.emotional_trend = "improving"
        else:
            s.emotional_trend = "stable"

        # Track low-risk streak for auto-expire of unresolved topics
        if (risk_level or "").lower() == "low":
            s._recent_low_turns += 1
        else:
            s._recent_low_turns = 0

        # Auto-expire unresolved topics after 3 consecutive low turns
        if s._recent_low_turns >= 3 and s.unresolved_topics:
            s.unresolved_topics.clear()

        now = _now_utc()

        # Extract symptoms (store tuple(term, timestamp)); dedupe by normalized term
        if extracted_symptoms:
            existing_prev_terms = {t for (t, _) in s.previous_symptoms}
            for sym in extracted_symptoms:
                term = normalize_term(sym)
                if not term:
                    continue
                if term not in existing_prev_terms:
                    s.previous_symptoms.append((term, now))
                    existing_prev_terms.add(term)

        # Active concerns (store tuple(term, timestamp)); dedupe by normalized term
        if condition_guess:
            term = normalize_term(condition_guess)
            if term:
                existing_concern_terms = {t for (t, _) in s.active_concerns}
                if term not in existing_concern_terms:
                    s.active_concerns.append((term, now))

        # Follow-ups: dedup unresolved
        if follow_up_question:
            q_norm = follow_up_question.strip()
            if q_norm:
                unresolved_questions = {
                    fu["question"]
                    for fu in s.prior_follow_ups
                    if (not fu.get("resolved", False))
                }
                if q_norm not in unresolved_questions:
                    s.prior_follow_ups.append(
                        {"question": q_norm, "resolved": False, "timestamp": now}
                    )

        # Unresolved topics escalation
        if condition_guess and (risk_level or "").lower() != "low":
            topic_term = normalize_term(condition_guess)
            if topic_term:
                existing = next(
                    (
                        t
                        for t in s.unresolved_topics
                        if normalize_term(t.get("topic", "")) == topic_term
                    ),
                    None,
                )
                if existing is None:
                    s.unresolved_topics.append(
                        {"topic": topic_term, "escalation_level": 1, "timestamp": now}
                    )
                else:
                    rl = (risk_level or "").lower()
                    if rl in {"critical", "high"}:
                        existing["escalation_level"] = int(
                            existing.get("escalation_level", 1)
                        ) + 1
                    existing["timestamp"] = now

        # Coping history expansion from emotion_label
        if emotion_label:
            el = emotion_label.lower()
            strategy = None
            if el in {"calm", "relieved"}:
                strategy = "breathing"
            elif el in {"anxious", "worried"}:
                strategy = "grounding"
            elif el in {"depressed", "sad"}:
                strategy = "journaling"
            elif el in {"frustrated", "angry"}:
                strategy = "exercise"

            if strategy:
                context = str(condition_guess or "").strip()
                s.coping_history.append(
                    {"strategy": strategy, "context": context, "timestamp": now}
                )

        return s


class SQLiteConversationStateStore(InMemoryConversationStateStore):
    """SQLite-backed conversation state store."""

    def __init__(self, db_path: Optional[Path] = None):
        super().__init__()

        base_dir = Path(__file__).resolve().parent.parent
        self.db_path = db_path or (base_dir / "data" / "neuronix_sessions.db")
        self.db_lock = threading.Lock()

        self._initialize_db()

    def _initialize_db(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.db_lock:
            conn = sqlite3.connect(
                str(self.db_path), check_same_thread=False, timeout=5.0
            )
            try:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversation_state (
                        user_id TEXT PRIMARY KEY,
                        previous_symptoms TEXT,
                        active_concerns TEXT,
                        prior_follow_ups TEXT,
                        unresolved_topics TEXT,
                        coping_history TEXT,
                        emotional_trend TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                conn.commit()
            finally:
                conn.close()

    @staticmethod
    def _serialize_dt(obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return obj

    def _snapshot_to_payload(self, snap: ConversationSnapshot) -> Dict[str, Any]:
        prev = [
            {"term": t, "timestamp": self._serialize_dt(ts)}
            for (t, ts) in snap.previous_symptoms
        ]
        concerns = [
            {"term": t, "timestamp": self._serialize_dt(ts)}
            for (t, ts) in snap.active_concerns
        ]

        def ser_list_of_dicts(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            out: List[Dict[str, Any]] = []
            for item in items:
                item2 = dict(item)
                for k, v in list(item2.items()):
                    item2[k] = self._serialize_dt(v)
                out.append(item2)
            return out

        return {
            "previous_symptoms": prev,
            "active_concerns": concerns,
            "prior_follow_ups": ser_list_of_dicts(snap.prior_follow_ups),
            "unresolved_topics": ser_list_of_dicts(snap.unresolved_topics),
            "coping_history": ser_list_of_dicts(snap.coping_history),
            "emotional_trend": snap.emotional_trend,
        }

    @staticmethod
    def _parse_dt(val: Any) -> Optional[datetime]:
        if not val:
            return None
        if isinstance(val, datetime):
            return val
        try:
            return datetime.fromisoformat(val)
        except Exception:
            return None

    def _payload_to_snapshot(self, payload: Dict[str, Any]) -> ConversationSnapshot:
        snap = ConversationSnapshot()
        snap.emotional_trend = payload.get("emotional_trend") or "stable"

        prev_list = payload.get("previous_symptoms") or []
        snap.previous_symptoms = [
            (x["term"], self._parse_dt(x.get("timestamp")) or _now_utc())
            for x in prev_list
            if x.get("term")
        ]

        concerns_list = payload.get("active_concerns") or []
        snap.active_concerns = [
            (x["term"], self._parse_dt(x.get("timestamp")) or _now_utc())
            for x in concerns_list
            if x.get("term")
        ]

        def parse_list(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            out: List[Dict[str, Any]] = []
            for item in items or []:
                item2 = dict(item)
                if "timestamp" in item2:
                    item2["timestamp"] = (
                        self._parse_dt(item2.get("timestamp")) or _now_utc()
                    )
                if "resolved_timestamp" in item2 and item2.get("resolved_timestamp"):
                    item2["resolved_timestamp"] = (
                        self._parse_dt(item2.get("resolved_timestamp"))
                        or item2.get("resolved_timestamp")
                    )
                out.append(item2)
            return out

        snap.prior_follow_ups = parse_list(payload.get("prior_follow_ups") or [])
        snap.unresolved_topics = parse_list(payload.get("unresolved_topics") or [])
        snap.coping_history = parse_list(payload.get("coping_history") or [])
        return snap

    def load_state(self, user_id: str) -> ConversationSnapshot:
        with self.db_lock:
            conn = sqlite3.connect(
                str(self.db_path), check_same_thread=False, timeout=5.0
            )
            conn.row_factory = sqlite3.Row
            try:
                row = conn.execute(
                    "SELECT * FROM conversation_state WHERE user_id = ?",
                    (user_id,),
                ).fetchone()
                if not row:
                    snap = self.get(user_id)
                    return snap

                payload = {
                    "previous_symptoms": json.loads(
                        row["previous_symptoms"] or "[]"
                    ),
                    "active_concerns": json.loads(row["active_concerns"] or "[]"),
                    "prior_follow_ups": json.loads(
                        row["prior_follow_ups"] or "[]"
                    ),
                    "unresolved_topics": json.loads(
                        row["unresolved_topics"] or "[]"
                    ),
                    "coping_history": json.loads(row["coping_history"] or "[]"),
                    "emotional_trend": row["emotional_trend"] or "stable",
                }

                snap = self._payload_to_snapshot(payload)
                self._store[user_id] = snap
                return snap
            finally:
                conn.close()

    def save_state(self, user_id: str, snap: ConversationSnapshot) -> None:
        payload = self._snapshot_to_payload(snap)
        with self.db_lock:
            conn = sqlite3.connect(
                str(self.db_path), check_same_thread=False, timeout=5.0
            )
            try:
                conn.execute(
                    """
                    INSERT INTO conversation_state (
                        user_id, previous_symptoms, active_concerns, prior_follow_ups,
                        unresolved_topics, coping_history, emotional_trend, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id) DO UPDATE SET
                        previous_symptoms=excluded.previous_symptoms,
                        active_concerns=excluded.active_concerns,
                        prior_follow_ups=excluded.prior_follow_ups,
                        unresolved_topics=excluded.unresolved_topics,
                        coping_history=excluded.coping_history,
                        emotional_trend=excluded.emotional_trend,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (
                        user_id,
                        json.dumps(payload["previous_symptoms"]),
                        json.dumps(payload["active_concerns"]),
                        json.dumps(payload["prior_follow_ups"]),
                        json.dumps(payload["unresolved_topics"]),
                        json.dumps(payload["coping_history"]),
                        payload["emotional_trend"],
                    ),
                )
                conn.commit()
            finally:
                conn.close()

    def update_from_cognitive_output(
        self,
        user_id: str,
        *,
        intent: str,
        flow_id: str,
        risk_level: str,
        condition_guess: Optional[str],
        emotion_label: Optional[str] = None,
        extracted_symptoms: Optional[List[str]] = None,
        follow_up_question: Optional[str] = None,
        retrieved_context_used: bool = False,
    ) -> ConversationSnapshot:
        snap = self.load_state(user_id)

        # Ensure internal rolling fields exist
        if snap._recent_risk_levels is None:
            snap._recent_risk_levels = []
        if snap._recent_low_turns is None:
            snap._recent_low_turns = 0

        # Temporarily set in-memory store reference to loaded snap
        self._store[user_id] = snap

        updated = super().update_from_cognitive_output(
            user_id,
            intent=intent,
            flow_id=flow_id,
            risk_level=risk_level,
            condition_guess=condition_guess,
            emotion_label=emotion_label,
            extracted_symptoms=extracted_symptoms,
            follow_up_question=follow_up_question,
            retrieved_context_used=retrieved_context_used,
        )

        self.save_state(user_id, updated)
        return updated

    def summarize_state(self, user_id: str) -> Dict[str, Any]:
        snap = self.load_state(user_id)

        symptoms = [
            f"{t} ({ts.date().isoformat()})" for (t, ts) in snap.previous_symptoms
        ]
        concerns = [
            f"{t} ({ts.date().isoformat()})" for (t, ts) in snap.active_concerns
        ]
        unresolved = [
            f"{u.get('topic')} (level {u.get('escalation_level', 1)})"
            for u in snap.unresolved_topics
            if u.get("topic")
        ]
        coping = [
            f"{c.get('strategy')} {('after ' + c.get('context')) if c.get('context') else ''}".strip()
            for c in snap.coping_history
        ]

        return {
            "symptoms": symptoms[-10:],
            "concerns": concerns[-10:],
            "trend": snap.emotional_trend,
            "unresolved": unresolved,
            "coping": coping[-10:],
        }

    def clear_state(self, user_id: str) -> None:
        snap = ConversationSnapshot()
        self._store[user_id] = snap
        self.save_state(user_id, snap)

    def mark_follow_up_resolved(self, user_id: str, question: str) -> None:
        snap = self.load_state(user_id)
        q_norm = (question or "").strip()
        if not q_norm:
            return

        now = _now_utc()
        for fu in snap.prior_follow_ups:
            if fu.get("question") == q_norm and not fu.get("resolved", False):
                fu["resolved"] = True
                fu["resolved_timestamp"] = now

        self.save_state(user_id, snap)


# ================================================================
# Global singleton (persistent)
# ================================================================
conversation_state_store = SQLiteConversationStateStore()

