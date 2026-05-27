# TODO: ontology_growth_engine learning component

- [x] Create `scripts/ontology_growth_engine.py` (LLM-free)
- [x] Implement pipeline:
  - [x] Load last N unknown-term events (default N=500)
  - [x] Cluster semantically similar phrases (embeddings if available; fallback otherwise)
  - [x] Enforce `MIN_CLUSTER_SIZE=3`
  - [x] Find nearest known ontology anchors (from `scripts/clinical_ontology.py`)
  - [x] Generate candidate suggestions (aliases) but **do not mutate** ontology
  - [x] Write outputs:
    - [x] `data/ontology_growth_suggestions.json`
    - [x] `data/ontology_review_queue.json` (default review-only mode)
- [ ] Add approval workflow (manual review approve/reject) to later stages
- [ ] Later: gate auto-accept behind confidence/cluster repetition thresholds
- [ ] Later: expand ontology seeds + run retrieval smoke tests

