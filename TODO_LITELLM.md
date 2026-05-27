# TODO - Enable LiteLLM content_policy_fallback

## Step 1 - Repo verification
- [x] Search repo for LiteLLM/Azure/LiteLLM config
- [x] Confirm no existing LiteLLM call sites

## Step 2 - Implement LiteLLM provider
- [ ] Update `llm_integration_wrapper.py` to support `provider="litellm"`
- [x] (Implementation) Add `content_policy_fallback` pass-through


- [ ] Add `_get_litellm_response(...)` implementation using `litellm.completion(...)`
- [ ] Wire `content_policy_fallback` (default from env: `LITELLM_CONTENT_POLICY_FALLBACK_MODEL`, fallback to `gpt-4.1-mini`)
- [ ] Add minimal logging of model/provider and whether fallback param was set

## Step 3 - (Optional) Route app calls through wrapper
- [ ] If required: update `backend/chat_engine.py` to use wrapper for any Azure-filtered provider path

## Step 4 - Testing
- [ ] Add `scripts/test_litellm_policy_fallback.py` to sanity check LiteLLM integration
- [ ] Run a quick smoke test

