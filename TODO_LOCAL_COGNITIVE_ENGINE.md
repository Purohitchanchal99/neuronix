# TODO: Local Cognitive Engine (LLM-free) 🧠

## Goal
Turn NEURONIX into a domain-specific, LLM-free cognitive pipeline.

## Step 1 — Disable external LLMs completely
- [x] Add runtime hard-gate in `scripts/cognitive_layer/cognitive_layer_v1.py` (fail fast if `NEURONIX_LLM_ENABLED=true`).
- [ ] Add env var default for apps/entrypoints (ensure nothing attempts to init Gemini/OpenAI when disabled).

## Step 2 — Intent classifier (local)
- [ ] Ensure `scripts/cognitive_layer/intent_classifier.py` can train/load cleanly.
- [ ] Add `train_intent_classifier.py` helper + minimal CLI.

## Step 3 — Emotion detector (local)
- [ ] Validate `scripts/cognitive_layer/emotion_detector.py` does not call external providers.

## Step 4 — Symptom extractor (local)
- [ ] Validate `scripts/cognitive_layer/symptom_extractor.py` outputs structured symptoms/duration.

## Step 5 — Conversation state
- [ ] Implement conversation_state module (dialogue turns, short-term memory, follow-up continuity).

## Step 6 — Reasoning + rules
- [x] Use `scripts/cognitive_layer/reasoning_engine.py` symbolic rules.

## Step 7 — Retrieval + grounding (Chroma)
- [ ] Wire retrieval filter by intent/domain if needed.
- [ ] Add adapter layer for stable Chroma interface (`similarity_search`).

## Step 8 — Response planner + template composer
- [ ] Ensure `response_planner.py` and `template_composer.py` cover: crisis, educational depression/anxiety, follow-up, recommendation.

## Step 9 — Safety layer
- [ ] Enforce crisis overrides even if classifier misfires.

## Step 10 — Integration with runtime
- [ ] Add a single orchestration entrypoint that uses Cognitive Layer v1 as the brain.
- [ ] Disable/avoid old LLM-based paths for production.

