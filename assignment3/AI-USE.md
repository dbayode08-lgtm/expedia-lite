# AI use disclosure: Assignment 3 (Steady)

| Tool | Model / version | Role |
|---|---|---|
| Claude (claude.ai, agent session with access to my laptop's Documents folder) | Claude Opus 5.5 (`claude-opus-5-5`) | Read my Expedia Lite repo to find patterns to reuse. Proposed the design and wrote most of the code (FastAPI backend, Vue frontend), the tests, the evaluation runner, the Playwright browser check, and first drafts of the docs and the three reports. Ran the tests and the browser walkthrough in its own sandbox. |
| Model used *inside* the app | Mock provider by default; OpenAI (`gpt-4o-mini`) or Anthropic (`claude-haiku-4-5`) when configured in `backend/.env` | Check-in reply + skill suggestion, optional reframe alternatives (see `docs/design.md` §3) |
| Mermaid CLI | mmdc (in the agent sandbox) | Rendered `docs/flow.mmd` to `docs/flow.png` |
| Playwright + ffmpeg | in the agent sandbox | Recorded and encoded the captioned demo video |

**How it was used.** The work was done in one long agent session on Oct 26–27, 2026. I gave the assignment brief and asked for all three parts. The agent built the app. I reviewed the design decisions and ran the app on my machine. On Nov 9 the agent also recorded the captioned demo/process video (`docs/recordings/demo.mp4`) automatically with Playwright (`e2e/record-demo.cjs`). The code explanation is the written walkthrough in `docs/code-walkthrough.md`, also drafted by the agent. There is no narrated recording. `docs/evidence-log.md` lists the prompts, failures and decisions. `docs/code-walkthrough.md` is the code I explain in the screencast.

**What I checked myself:** I started the app on my Mac with `start-steady.command` and confirmed the start screen loaded and the backend responded (Oct 26). I ran `submit-a3.command` to push the `assignment3` branch to GitHub and submitted Part 3.2. For Part 3.3 I reviewed the demo video before submitting.

No credentials, personal data or research-participant data were shared with any AI tool. All test inputs are fictional.
