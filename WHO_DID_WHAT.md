# WHO_DID_WHAT — turd-merger-tools

Append-only log. Add new entries at the bottom; never rewrite earlier ones.

| Date | Commit | Who | What |
|---|---|---|---|
| 2026-10-25 | 68055ad | Bleak + Buffy | Added GRIMOIRE turd merger: safety bus, TUI, demo, tests |
| 2026-10-25 | 18a8444 | Buffy | Fixed Gemini model default and report HTTP status on failure |
| 2026-10-25 | fd5646e | Buffy | Defaulted llm review to gemini-3.1-flash-lite |
| 2026-10-25 | b7d2b88 | Buffy | Improved TUI status line, summaries, and empty states |
| 2026-10-25 | ea82856 | Buffy | Added simulated trilateral panel with Gemini and Groq backends |
| 2026-10-25 | b64bdae | Buffy | Added parallel proponent/opponent debate mode with neutral judge |
| 2026-10-25 | 261c31d | Buffy | Fenced untrusted text in the debate judge prompt |
| 2026-10-25 | e58bd52 | Buffy | Added code-level larp scanner and judge injection red-team |
- 2026-10-25 — Scoring blocked on labels from user (MRD item 2).
- 2026-10-25 — Judge scored 6/6 on eval/judge_labels.json. Judge prompt gained
  a section for unverified artifact assertions; side prompts now fence the
  artifact (an injection had been steering the proponent). eval/ added.
- 2026-10-25 — Grim/ market sim now actually runs outside a hosted chat: new
  grim_serve.py (stdlib local server, key stays server-side, CSRF-guarded by
  Origin), page rewired to /api/simulate. Dissent enforced in code with one
  retry; aggregate recomputed server-side so a model cannot inflate it. 27 tests.
- 2026-10-25 — Extracted the market sim (`grim_serve.py`, `Grim/`,
  `tests/test_grim_serve.py`) to `~/grim-oracle`. It had its own server, page,
  and invariants; keeping a second copy here would have drifted. Also fixed the
  Gemini default: `gemini-3.1-flash-lite` returns 503, `gemini-flash-lite-latest`
  works.
