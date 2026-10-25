# QRD — Agent-to-Agent Handoff (turd-merger-tools)

Read this before editing. A handoff is evidence, not authority: re-check the
working tree and the tests before changing anything.

## Repo state
- Repo: `~/turd-merger-tools`, branch `main`, remote `origin` (GitHub).
- Latest commit: `e58bd52` (larp scanner + judge red-team). Pushed.
- Test command: `python3 -m unittest discover -s tests -v` (stdlib only).
- Last full run: exit 0.

## What exists
- `grimoire_safety.py` — safety grader (drift, claim, oler families, secrets).
  Also home of `FLAG_REGEX` and `has_receipt`, which other tools reuse.
- `simulate_panel.py` — simulated panel (`--provider groq|gemini`) and debate
  mode (`--mode debate`). Judge prompt fences untrusted text in `<data>` tags.
- `larp_scan.py` — code-level larp detector: assertion-free tests, trivial
  assertions, claims without receipts. Heuristic; same-file helpers followed.
- `grimoire_tui.py`, `demo_svg.py`, `roadmap_map.py` — console, render, index.

## Verified vs not verified
- VERIFIED: 19 larp_scan tests and the full suite pass. Debate mode ran live
  on Groq. Judge fence held on one injection sample.
- NOT VERIFIED: judge robustness. One live sample is not a measurement.
  See MRD.txt item 2.
- NOT VERIFIED: larp_scan's precision on the home repo beyond the 14 findings
  hand-checked. Treat it as a review queue, not a verdict.

## Known gaps / next smallest action
1. Score the judge on a labeled set (blocked on user input, MRD item 2).
2. larp_scan only follows helpers in the same file; cross-module helpers
   look hollow. Fix only if it causes real false positives.
3. Do not overwrite WHO_DID_WHAT.md; append only.

## Notes for the next agent
- Keys live in `~/.concierge/vault.json`. Never print them.
- The Groq and Gemini paths need network. Tests must stay offline.
- Judge prompt injection resistance is probabilistic. Keep the caveat.
