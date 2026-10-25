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
- `grim_serve.py` — local HTTP server for the market sim. Serves
  `Grim/grim_market_sim.html`, proxies Groq/Gemini, keeps the key server-side.
- `eval/` — judge scoring harness + labeled baseline; `--recheck` re-scores
  saved transcripts without spending a call.

## Market sim invariants (do not weaken these)
- The browser never receives a key and never calls a provider directly.
- The aggregate is recomputed in `normalize()`; the model's own aggregate is
  discarded. Do not start trusting it.
- Dissent is enforced in code (`has_dissent`) with one strict retry. A run with
  no objection reports `dissent_found: false`. Never synthesize agreement to
  fill the gap.
- POSTs with a non-local `Origin` are refused, so a random web page cannot
  spend this machine's credits.

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
