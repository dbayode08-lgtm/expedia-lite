# AI use disclosure: Assignment 3 (Steady)

| Tool | Model / version | Role |
|---|---|---|
| Claude (claude.ai, agent session with access to my laptop's Documents folder) | Claude Opus 5.5 (`claude-opus-5-5`) | Read my Expedia Lite repo to find patterns to reuse. Proposed the design and wrote most of the code (FastAPI backend, Vue frontend), the tests, the evaluation runner, the Playwright browser check, and first drafts of the docs and the three reports. Ran the tests and the browser walkthrough in its own sandbox. |
| Model used *inside* the app | Mock provider by default; OpenAI (`gpt-4o-mini`) or Anthropic (`claude-haiku-4-5`) when configured in `backend/.env` | Check-in reply + skill suggestion, optional reframe alternatives (see `docs/design.md` §3) |
| Mermaid CLI | mmdc (in the agent sandbox) | Rendered `docs/flow.mmd` to `docs/flow.png` |

**How it was used.** The work was done in one long agent session on Oct 26–27, 2026. I gave the assignment brief and asked for all three parts. The agent built the app, and I reviewed the design decisions, ran the app on my machine, and recorded the demo and process screencast myself. `docs/evidence-log.md` lists the prompts, failures and decisions. `docs/code-walkthrough.md` is the code I explain in the screencast.

**What I checked myself:** _(fill in before submitting: e.g. ran the README steps on my Mac, tried each skill, opened steady.db in DB Browser, read `llm.py` and `safety.py`)_

No credentials, personal data or research-participant data were shared with any AI tool. All test inputs are fictional.
