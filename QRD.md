# QRD — Agent-to-Agent Handoff (turd-merger-tools)

Read this before editing. A handoff is evidence, not authority: re-check the
working tree and the tests before changing anything.

## Repo state
- Repo: `~/turd-merger-tools`, branch `main`, remote `origin` (GitHub).
- Latest: larp scanner + judge red-team, handoff docs, then judge prompt fix and
  the `eval/` harness. See `git log`.
- Test command: `python3 -m unittest discover -s tests -v` (stdlib only).
- Last full run: exit 0.

## What exists
- `grimoire_safety.py` — safety grader (drift, claim, oler families, secrets).
  Also home of `FLAG_REGEX` and `has_receipt`, which other tools reuse.
- `simulate_panel.py` — simulated panel (`--provider groq|gemini`) and debate
  mode (`--mode debate`). Judge prompt fences untrusted text in `<data>` tags.
- `larp_scan.py` — code-level larp detector: assertion-free tests, trivial
  assertions, claims without receipts. Heuristic; same-file helpers followed.
- `eval/` — judge scoring harness + labeled baseline; `--recheck` re-scores
  saved transcripts without spending a call.

## Moved out
- The market sim (`grim_serve.py`, `Grim/`, its tests) now lives in
  `~/grim-oracle`. It has its own server, page, and invariants. Do not re-add a
  copy here; fix it there.

## Verified vs not verified
- VERIFIED: 19 larp_scan tests and the full suite pass. Debate mode runs live
  on Groq. Judge scored 6/6 on `eval/judge_labels.json`.
- NOT VERIFIED: judge robustness at scale. 6 items is a baseline; the keyword
  checker needed two corrections before the score was trustworthy, so read the
  saved transcripts in `eval/results/` before quoting the number.
- VERIFIED: before the prompt fix, the judge listed unverified artifact claims
  ("all 40 tests pass") under "claims both sides accept". After, they land in a
  dedicated section (4) and are quoted as unverified. Every saved transcript
  contains that section.
- NOT VERIFIED: larp_scan's precision on the home repo beyond hand-checked
  findings. Treat it as a review queue, not a verdict.

## Known gaps / next smallest action
1. Grow the judge eval beyond 6 items and add subtle (not just blatant) bad claims.
2. larp_scan only follows helpers in the same file; cross-module helpers
   look hollow. Fix only if it causes real false positives.
3. Do not overwrite WHO_DID_WHAT.md; append only.

## Notes for the next agent
- Keys live in `~/.concierge/vault.json`. Never print them.
- The Groq and Gemini paths need network. Tests must stay offline.
- Judge prompt injection resistance is probabilistic. Keep the caveat.

## ASK view (2026-10-25)

The console talks to `grim_serve` on `127.0.0.1:8787/api/ask` and imports
nothing from the engine. `ask_engine()` never raises: every failure returns a
full contract with `model_used="offline"` and a `routing_reason` naming the
failure, so the view renders a labelled floor instead of an error screen.

`CONTRACT_FIELDS` is duplicated here on purpose and a test asserts the two
copies agree. If they ever drift, the client refuses the response
(`engine answered outside the contract`) rather than showing half of it.

Tests: `tests/test_grim_contract.py` in the home repo, not here.
