# NEURONIX Eval Harness (Phase C.6)

This folder is for a formal evaluation harness to measure runtime quality and safety across your multiple pipelines.

## Metrics to track (per your spec)
- hallucination rate
- DSM coverage
- follow-up quality
- grounding accuracy
- crisis-detection recall
- latency
- retrieval precision

## Expected deliverables
- A single CLI entrypoint: `python -m eval_harness.run`
- Output: `eval_results.jsonl` + summary `eval_results_summary.json`

## Notes
- Use the same test set across runtimes.
- Store run config (commit hash, runtime name, vector_store name, embedding model).

