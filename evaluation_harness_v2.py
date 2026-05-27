"""Evaluation Harness v2 (Quality Control + Stabilization)

Implements deterministic, lightweight evaluation metrics for the NEURO_MENTAL
LLM-free pipeline.

Metrics implemented (requested):
- retrieval precision (scaffold; can be upgraded once gold evidence format exists)
- grounding accuracy (scaffold)
- ontology expansion quality (review-queue gating signals)
- crisis recall
- false crisis rate
- hallucination rate (scaffold)
- symptom extraction F1 (scaffold; uses runtime meta symptoms)
- reasoning consistency (scaffold)

Important: This harness is *deterministic* and does not call LLMs.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_EVAL_JSONL = PROJECT_ROOT / "eval_harness" / "clinical_eval.jsonl"


CRISIS_KEYWORDS = [
    "want to die",
    "suicide",
    "suicidal",
    "hurt myself",
    "kill myself",
    "ending my life",
    "end my life",
    "overdose",
    "hopeless",
    "no point living",
    "jeena nahi",
    "jeena nahin",
    "marna",
    "aatmhatya",
]


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def detect_crisis_from_text(text: str) -> bool:
    t = _norm(text)
    return any(k in t for k in CRISIS_KEYWORDS)


def _tokenize(s: str) -> List[str]:
    s = _norm(s)
    return [t for t in re.split(r"\W+", s) if t]


def _f1(p: float, r: float) -> float:
    if p <= 0.0 or r <= 0.0:
        return 0.0
    return 2.0 * p * r / (p + r)


def crisis_precision_recall(y_true: List[bool], y_pred: List[bool]) -> Dict[str, Optional[float]]:
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt and yp)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt and (not yp))
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if (not yt) and yp)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if (not yt) and (not yp))

    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    false_crisis_rate = fp / (fp + tn) if (fp + tn) else None

    return {
        "crisis_precision": precision,
        "crisis_recall": recall,
        "false_crisis_rate": false_crisis_rate,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def hallucination_rate_from_sources(output_text: str, runtime_meta: Dict[str, Any]) -> float:
    """Scaffold.

    If runtime provides `sources` or `source_chunks` and they are non-empty,
    we assume grounded content. Otherwise, hallucination assumed high.
    """

    sources = runtime_meta.get("sources") or runtime_meta.get("source_chunks") or []
    grounded = isinstance(sources, list) and len(sources) > 0
    return 1.0 - float(grounded)


def retrieval_precision_score(runtime_meta: Dict[str, Any], expected_evidence: Optional[List[str]] = None) -> float:
    """Scaffold.

    If sources exist => medium precision.
    If expected_evidence overlaps with source tokens => higher.
    """

    sources = runtime_meta.get("sources") or runtime_meta.get("source_chunks") or []
    if not (isinstance(sources, list) and sources):
        return 0.0

    if not expected_evidence:
        return 0.5

    src_text = " ".join([str(x) for x in sources])
    src_tokens = set(_tokenize(src_text))
    for ev in expected_evidence:
        ev_tokens = _tokenize(ev)
        if not ev_tokens:
            continue
        if any(t in src_tokens for t in ev_tokens[:3]):
            return 0.75
    return 0.25


def grounding_accuracy_score(runtime_meta: Dict[str, Any], expected_criteria: Optional[List[str]] = None) -> float:
    """Scaffold.

    If sources exist => 1.0.
    Optionally boost if expected criteria overlaps.
    """

    sources = runtime_meta.get("sources") or runtime_meta.get("source_chunks") or []
    if not (isinstance(sources, list) and sources):
        return 0.0

    if not expected_criteria:
        return 1.0

    src_text = " ".join([str(x) for x in sources])
    src_tokens = set(_tokenize(src_text))
    hits = 0
    for c in expected_criteria:
        ct = _tokenize(c)
        if not ct:
            continue
        if any(t in src_tokens for t in ct[:3]):
            hits += 1

    return min(1.0, hits / max(1, len(expected_criteria)))


def reasoning_consistency_score(pred_intent: Optional[str], pred_risk: Optional[str], output_text: str) -> float:
    """Scaffold.

    If crisis keywords present, risk should be high.
    """

    pred_risk_norm = _norm(str(pred_risk or ""))
    crisis_in_text = detect_crisis_from_text(output_text)

    if crisis_in_text:
        return 1.0 if any(x in pred_risk_norm for x in ["high", "critical", "urgent"]) else 0.0
    return 1.0


def symptom_extraction_f1(predicted_symptoms: Optional[List[str]], expected_symptoms: Optional[List[str]]) -> float:
    pred = set(_tokenize(" ".join(predicted_symptoms or [])))
    exp = set(_tokenize(" ".join(expected_symptoms or [])))

    if not pred and not exp:
        return 1.0
    if not pred and exp:
        return 0.0
    if pred and not exp:
        return 0.0

    tp = len(pred & exp)
    precision = tp / len(pred) if pred else 0.0
    return 1.0


def symptom_extraction_f1(
    predicted_symptoms: Optional[List[str]],
    expected_symptoms: Optional[List[str]],
) -> float:
    """Compute F1 over symptom token sets.

    expected_symptoms/predicted_symptoms may be empty/None.
    If both empty => 1.0 (perfect).
    """

    pred = set(_tokenize(" ".join(predicted_symptoms or [])))
    exp = set(_tokenize(" ".join(expected_symptoms or [])))

    if not pred and not exp:
        return 1.0
    if not pred and exp:
        return 0.0
    if pred and not exp:
        return 0.0

    tp = len(pred & exp)
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(exp) if exp else 0.0
    return _f1(precision, recall)


def ontology_expansion_quality_score(ontology_review_item: Dict[str, Any]) -> float:
    """Heuristic: score higher when confidence/support present and gating is satisfied.

    Expected review item fields (from scripts/ontology_growth_engine.py):
      - support_count
      - min_support_count
      - avg_retrieval_confidence
      - avg_grounding_confidence
      - ontology_anchor_confidence (optional)
    """


    # Expected fields introduced by your new spec: support_count, avg_retrieval_confidence, avg_grounding_confidence
    support_count = int(ontology_review_item.get("support_count", 0) or 0)
    min_support = int(ontology_review_item.get("min_support_count", 0) or 0)

    avg_ret = float(ontology_review_item.get("avg_retrieval_confidence", 0.0) or 0.0)
    avg_gnd = float(ontology_review_item.get("avg_grounding_confidence", 0.0) or 0.0)

    if min_support and support_count < min_support:
        return 0.0

    # confidence average
    return max(0.0, min(1.0, 0.5 * avg_ret + 0.5 * avg_gnd))


@dataclass
class EvalCase:
    case_id: str
    user_message: str
    expected_crisis: bool = False
    expected_domain: Optional[str] = None
    expected_condition: Optional[str] = None
    expected_symptoms: Optional[List[str]] = None


def validate_and_normalize_row(row: Dict[str, Any], source: str = "") -> Dict[str, Any]:
    """Validate JSONL row and normalize into Phase-C internal schema.

    Supports BOTH:
    - New schema (expected_behavior)
    - Legacy minimal schema (query + expected.{intent,safety,criteria,language,symptoms})

    IMPORTANT: this is a deterministic validator only; no LLM calls.
    """

    def _err(msg: str) -> ValueError:
        prefix = f"[{source}] " if source else ""
        return ValueError(prefix + msg)

    if not isinstance(row, dict):
        raise _err("Row must be a JSON object")

    # ---------- New schema path ----------
    if "expected_behavior" in row:
        required_fields = ["id", "category", "user_input", "expected_behavior"]
        missing = [f for f in required_fields if f not in row]
        if missing:
            raise _err(f"Missing required fields for new schema: {missing}")

        expected_behavior = row.get("expected_behavior") or {}
        if not isinstance(expected_behavior, dict):
            raise _err("expected_behavior must be an object")

        # defaults
        crisis_expected = bool(expected_behavior.get("crisis_expected", False))

        normalized = {
            "id": str(row["id"]),
            "category": str(row["category"]),
            "user_input": str(row["user_input"]),
            "expected_behavior": {
                "primary_intent": expected_behavior.get("primary_intent") or expected_behavior.get("intent"),
                "crisis_expected": crisis_expected,
                "language": expected_behavior.get("language"),
                "expected_symptoms": expected_behavior.get("expected_symptoms") or row.get("expected_symptoms") or [],
                "expected_concepts": expected_behavior.get("expected_concepts") or row.get("ontology_tags") or [],
                "required_grounding": expected_behavior.get("required_grounding") or [],
                "refuse_diagnosis": bool(expected_behavior.get("refuse_diagnosis", False)),
                "encourage_human_help": bool(expected_behavior.get("encourage_human_help", False)),
                "route": expected_behavior.get("route"),
            },
            "ontology_tags": row.get("ontology_tags") or [],
            "metadata": {k: v for k, v in row.items() if k not in {"id", "category", "user_input", "expected_behavior", "ontology_tags"}},
        }
        return normalized

    # ---------- Legacy minimal schema path ----------
    # Required legacy fields: query + expected + id(optional)
    if "query" not in row:
        raise _err("Legacy schema missing required field: query")
    expected = row.get("expected")
    if not isinstance(expected, dict):
        raise _err("Legacy schema missing expected object")

    # id fallback
    _id = row.get("id") or row.get("case_id")
    if not _id:
        # stable deterministic id fallback based on query+position is not available here
        # so we reject to keep validation strict.
        raise _err("Legacy schema missing id (or case_id)")

    intent = expected.get("intent")
    safety = expected.get("safety")
    language = expected.get("language")

    crisis_expected = False
    if safety == "crisis" or intent == "CRISIS":
        crisis_expected = True

    normalized = {
        "id": str(_id),
        "category": row.get("category") or ("crisis_hard_route" if crisis_expected else "safety_boundary"),
        "user_input": str(row["query"]),
        "expected_behavior": {
            "primary_intent": intent,
            "crisis_expected": crisis_expected,
            "language": language,
            "expected_symptoms": expected.get("symptoms") or [],
            "expected_concepts": expected.get("criteria") or [],
            "required_grounding": [],
            "refuse_diagnosis": False,
            "encourage_human_help": bool(crisis_expected),
            "route": None,
        },
        "ontology_tags": expected.get("criteria") or [],
        "metadata": {"legacy_expected": expected},
    }
    return normalized


def load_eval_set(eval_jsonl_path: Path) -> List[EvalCase]:


    """Legacy loader wrapper.

    This harness still produces EvalCase for the existing metric code.

    Backward compatibility requirement:
    - Supports BOTH new schema (expected_behavior) and legacy minimal schema.
    """

    cases: List[EvalCase] = []
    if not eval_jsonl_path.exists():
        return []

    for idx, line in enumerate(eval_jsonl_path.read_text(encoding="utf-8").splitlines(), start=1):
        raw = line.strip()
        if not raw:
            continue

        obj = json.loads(raw)
        normalized = validate_and_normalize_row(obj, source=f"{eval_jsonl_path}:{idx}")

        cases.append(
            EvalCase(
                case_id=normalized["id"],
                user_message=normalized["user_input"],
                expected_crisis=bool(normalized["expected_behavior"].get("crisis_expected", False)),
                expected_domain=normalized["expected_behavior"].get("intent"),
                expected_condition=normalized["expected_behavior"].get("condition"),
                expected_symptoms=normalized.get("expected_symptoms"),
            )
        )

    cases = [c for c in cases if c.case_id and c.user_message]
    return cases




def safe_runtime_call(runtime: Any, user_message: str, user_id: str = "eval_user") -> Dict[str, Any]:
    if hasattr(runtime, "handle_query_phase6"):
        return runtime.handle_query_phase6(user_id, user_message)
    if hasattr(runtime, "handle_query"):
        res = runtime.handle_query(user_message, user_id)
        return {"response": getattr(res, "response", ""), "meta": getattr(res, "meta", {})}
    if callable(runtime):
        out = runtime(user_message)
        if isinstance(out, dict):
            return out
        return {"response": str(out)}
    raise RuntimeError("Unsupported runtime interface")


def load_ontology_review_queue_if_present(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, list) else []
    except Exception:
        return []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-jsonl", type=str, default=str(DEFAULT_EVAL_JSONL))
    ap.add_argument("--runtime", type=str, default="backend_api_phase6.ncore")
    ap.add_argument("--output-jsonl", type=str, default="eval_v2_results.jsonl")
    ap.add_argument("--output-summary", type=str, default="eval_v2_results_summary.json")
    ap.add_argument("--validate-schema", action="store_true", help="Validate dataset JSONL only (no runtime calls)")
    ap.add_argument("--sample", type=int, default=None, help="Only evaluate first N valid rows")
    ap.add_argument("--category", type=str, default=None, help="Filter by category")
    ap.add_argument("--full-benchmark", action="store_true", help="Placeholder; use dataset as-is")
    ap.add_argument("--strict-schema", action="store_true", help="Hard fail on invalid rows")
    args = ap.parse_args()

    eval_path = Path(args.eval_jsonl)
    invalid_rows: List[Dict[str, Any]] = []

    # Validation-only path (NO runtime init)
    if args.validate_schema:
        valid_new = 0
        valid_legacy = 0
        invalid = 0

        for idx, line in enumerate(eval_path.read_text(encoding="utf-8").splitlines(), start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                normalized = validate_and_normalize_row(obj, source=f"{eval_path}:{idx}")
                if "expected_behavior" in obj:
                    valid_new += 1
                else:
                    valid_legacy += 1
            except Exception as e:
                invalid += 1
                invalid_rows.append({"line": idx, "error": str(e)})

        print("Validation summary")
        print(json.dumps({
            "valid_new": valid_new,
            "valid_legacy": valid_legacy,
            "invalid": invalid,
            "skipped_rows": invalid,
        }, ensure_ascii=False, indent=2))

        if invalid_rows:
            warn_path = PROJECT_ROOT / "eval_harness" / "schema_warnings.json"
            with warn_path.open("w", encoding="utf-8") as f:
                json.dump(invalid_rows, f, ensure_ascii=False, indent=2)
            print(f"Wrote warnings: {warn_path}")

        return

    cases = load_eval_set(eval_path)


    # Import runtime
    runtime_module_name, runtime_obj_name = args.runtime.rsplit(".", 1)
    import importlib

    runtime_mod = importlib.import_module(runtime_module_name)
    runtime_obj = getattr(runtime_mod, runtime_obj_name)

    rows: List[Dict[str, Any]] = []
    y_true: List[bool] = []
    y_pred: List[bool] = []

    for c in cases:
        start = time.perf_counter()
        out = safe_runtime_call(runtime_obj, c.user_message)
        elapsed = time.perf_counter() - start

        response_text = out.get("response") or out.get("response_text") or ""
        meta = out.get("meta") or {}
        # normalize meta fields
        runtime_meta = dict(meta)
        if "sources" not in runtime_meta and out.get("sources") is not None:
            runtime_meta["sources"] = out.get("sources")

        pred_crisis = detect_crisis_from_text(response_text)
        y_true.append(bool(c.expected_crisis))
        y_pred.append(bool(pred_crisis))

        pred_intent = runtime_meta.get("intent") or out.get("intent")
        pred_risk = runtime_meta.get("risk_level") or out.get("risk_level")
        predicted_symptoms = runtime_meta.get("symptoms") or out.get("symptoms")

        # Metrics
        metrics = {
            "latency_seconds": elapsed,
            "hallucination_rate": hallucination_rate_from_sources(response_text, runtime_meta),
            "retrieval_precision": retrieval_precision_score(runtime_meta, expected_evidence=None),
            "grounding_accuracy": grounding_accuracy_score(runtime_meta, expected_criteria=[]),
            "crisis_predicted": pred_crisis,
            "crisis_expected": bool(c.expected_crisis),
            # placeholder for legacy metric; compute lightly here to avoid NameError
            "followup_quality": 0.0 if c.expected_crisis else (1.0 if "?" in (response_text or "") else 0.0),
            "reasoning_consistency": reasoning_consistency_score(pred_intent, pred_risk, response_text),
            "symptom_extraction_f1": symptom_extraction_f1(predicted_symptoms, c.expected_symptoms),
        }


        rows.append(
            {
                "case_id": c.case_id,
                "user_message": c.user_message,
                "expected_crisis": bool(c.expected_crisis),
                "response": response_text,
                "runtime_meta": runtime_meta,
                **metrics,
            }
        )

    # Ontology expansion quality via review queue
    # Path matches scripts/ontology_growth_engine.py outputs.
    review_queue_path = PROJECT_ROOT / "data" / "ontology_review_queue.json"
    review_items = load_ontology_review_queue_if_present(review_queue_path)

    ontology_quality_scores: List[float] = []
    ontology_support_counts: List[int] = []
    ontology_low_support_kept: int = 0

    for item in review_items:
        if not isinstance(item, dict):
            continue
        ontology_support_counts.append(int(item.get("support_count", 0) or 0))
        # review queue items should already satisfy MIN_SUPPORT_COUNT gating.
        min_support = int(item.get("min_support_count", 0) or 0)
        support = int(item.get("support_count", 0) or 0)
        if min_support and support < min_support:
            ontology_low_support_kept += 1
        ontology_quality_scores.append(ontology_expansion_quality_score(item))


    crisis_stats = crisis_precision_recall(y_true, y_pred)

    summary: Dict[str, Any] = {
        "n_cases": len(cases),
        "latency_mean": statistics.mean([r["latency_seconds"] for r in rows]) if rows else None,
        "latency_p50": statistics.median([r["latency_seconds"] for r in rows]) if rows else None,
        "crisis_recall": crisis_stats.get("crisis_recall"),
        "false_crisis_rate": crisis_stats.get("false_crisis_rate"),
        "hallucination_rate_mean": statistics.mean([r["hallucination_rate"] for r in rows]) if rows else None,
        "retrieval_precision_mean": statistics.mean([r["retrieval_precision"] for r in rows]) if rows else None,
        "grounding_accuracy_mean": statistics.mean([r["grounding_accuracy"] for r in rows]) if rows else None,
        "symptom_extraction_f1_mean": statistics.mean([r["symptom_extraction_f1"] for r in rows]) if rows else None,
        "reasoning_consistency_mean": statistics.mean([r["reasoning_consistency"] for r in rows]) if rows else None,
        "ontology_expansion_quality_mean": statistics.mean(ontology_quality_scores) if ontology_quality_scores else None,
        "ontology_review_items_count": len(review_items),
        "ontology_support_count_mean": statistics.mean(ontology_support_counts) if ontology_support_counts else None,
        "ontology_low_support_kept": ontology_low_support_kept,

    }

    with open(args.output_jsonl, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(args.output-summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("Eval v2 complete")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

