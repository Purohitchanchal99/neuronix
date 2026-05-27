# TODO — Crisis Hard-Routing + Canonical Benchmark Migration

## Phase 1 — Canonical Evaluation Schema
- [ ] Update `eval_harness/clinical_eval.jsonl` to ONE canonical schema:
  - `query`, `category`, `expected_intent`, `expected_concepts`, `expected_risk_level`, `must_include`, `must_not_include`, `ground_truth_type`, `crisis_expected`
- [ ] Update `eval_harness/evaluation_harness_v2.py`:
  - accept canonical rows (and keep legacy normalization TEMPORARILY)
  - compute separate crisis metrics
  - add `unsafe_response_rate` scaffold

## Phase 2 — Deterministic Crisis Hard-Routing
- [ ] Implement deterministic `risk_classifier()` (rule-based now) in backend routing layer
- [ ] Add crisis route that is LLM/RAG/ontology/planner free:
  - never uses retrieval, embeddings, grounding, ontology expansion, or planner
  - returns fixed safe templates + emergency guidance
- [ ] Wire crisis routing into:
  - `backend_api_phase6.py` (text + voice path)
  - `hybrid_routing_system.py` only if required by architecture

## Phase 3 — Safety Attack Benchmarking
- [ ] Extend `eval_harness/clinical_eval.jsonl` with `safety_attack` + subcategories:
  - `medication_bait`, `self_harm_instruction`, `violent_intent`, `hallucination_trap`, `diagnosis_trap`
  - add `must_not_include` requirements (e.g., dosage/instructions)

## Phase 4 — Metrics Expansion
- [ ] Update `evaluation_harness_v2.py` to compute:
  - `crisis_recall`, `crisis_precision`, `unsafe_response_rate`
  - separate reporting by `category`
- [ ] Add parsing checks for safety violations (deterministic regex-based) to support unsafe rate.

## Verification
- [ ] Run schema validation on eval JSONL (no runtime calls).
- [ ] Run harness end-to-end for a small sample.
- [ ] Run unit tests present in repo (at least compilation).

