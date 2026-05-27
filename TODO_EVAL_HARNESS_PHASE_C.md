# TODO: Eval Harness Phase C (Retrieval + Grounding Expansion)

## Plan Summary
1. Expand `eval_harness/clinical_eval.jsonl` into a large structured dataset.
2. Update `evaluation_harness_v2.py` (and any other loaders) to support the new JSONL schema.
3. Add Crisis Hard-Routing evaluation coverage (HIGH RISK => skip retrieval/ontology/grounding; immediate crisis response).
4. Keep ontology/grounding evaluation scaffolds compatible with the new dataset fields.

## Step-by-step Checklist
- [ ] Inspect current `eval_harness/clinical_eval.jsonl` and confirm existing schema.
- [ ] Inspect `evaluation_harness_v2.py` loader + expected schema.
- [ ] Implement new dataset schema per task:
  - [ ] categories: depression definition, anxiety symptoms, insomnia complaints, Hinglish symptom phrasing, typo/noisy inputs, suicide/crisis, violence risk, coping guidance, DSM-style informational questions, multi-symptom mixed queries, ambiguous emotional statements
  - [ ] per-sample fields: query, expected_intent, expected_concepts[], expected_risk_level, must_include[], must_not_include[], ground_truth_type
- [ ] Replace `eval_harness/clinical_eval.jsonl` with structured/balanced large set.
- [ ] Update `evaluation_harness_v2.py` to read new schema fields and compute/record:
  - [ ] must_include/must_not_include compliance (where runtime supports it)
  - [ ] crisis routing expectation evaluation (high risk -> crisis-only response)
- [ ] Add/update any scripts that depend on the old JSONL structure (e.g., graders/runners).
- [ ] Run `python eval_harness/run.py` and/or `python evaluation_harness_v2.py` to validate end-to-end.
- [ ] Update `eval_results_summary.json` / sample outputs for sanity.

