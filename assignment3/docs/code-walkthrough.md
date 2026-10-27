# Code walkthrough (for the screencast: "explain a relevant piece of generated code")

## `run_model()` in `backend/app/llm.py`

This is where the model is allowed to contribute, and where it is kept from breaking anything.

```python
def run_model(purpose, system, user, mock_raw, validator, session_id=None, simulate_failure=False):
    conn = get_conn()
    provider = "fail" if simulate_failure else effective_provider(conn)   # (1)
    try:
        if provider == "fail": raise ModelError("simulated_failure ...")
        if provider == "openai":   _bump_live_calls(conn); raw = call_openai(system, user)   # (2)
        elif provider == "anthropic": _bump_live_calls(conn); raw = call_anthropic(system, user)
        else: raw = mock_raw                                                  # (3)
        data = validator(raw)                                                 # (4)
    except httpx.TimeoutException: error = "timeout"                          # (5)
    except httpx.HTTPError as e:  error = f"network: ..."
    except ModelError as e:       error = str(e)
    except Exception as e:        error = f"unexpected: ..."
    INSERT INTO model_calls (...)                                              # (6)
    if error: return {}, "fallback", error                                    # (7)
    return data, "live_model" or "mock", None
```

1. **`effective_provider`** reads `LLM_PROVIDER`. If live calls already used ≥ `LIVE_CALL_LIMIT` (count stored in SQLite `app_state`), it returns `"mock"`. That's how the 50-call cap works even across restarts.
2. The counter goes up **before** the call, so a failed paid call still counts toward the cap.
3. Mock mode uses a deterministic answer (keyword rules), so tests and peer testing cost nothing.
4. **The validator is the real guardrail, not the prompt.** `validate_checkin` requires JSON, ≤ 280 chars, ≤ 2 sentences, a skill from the fixed list, and none of the banned patterns ("!", "you should", "therap", "diagnos", …). A prompt can be ignored by the model; this check can't.
5. Every failure type becomes a string, never an exception that reaches the user. The timeout is 6 s (`MODEL_TIMEOUT_SECONDS`).
6. Every attempt is logged (`model_calls`). This is the evidence I used for the failure demo.
7. On failure the route shows a fixed fallback line ("The text helper isn't available right now…"), and the four skills and Crisis support keep working.

**What runs before this:** `routes.chat()` calls `is_crisis_text()` first. If it matches, `run_model` is never called, so crisis-like text never goes to a model.

## Crisis regex (`shared/crisis.json`, used by `app/safety.py` and `frontend/src/safety.js`)

One JSON file, two readers: Python (`re`, ignore case) and the browser (`RegExp(p, "i")`). The browser check means crisis text opens Crisis support even with the backend down. The Crisis support **button** doesn't use the regex at all.
