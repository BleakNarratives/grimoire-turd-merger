# ROADMAP — turd-merger-tools

Status key: [x] done and verified · [ ] not done · [~] partly done.

## Phase 1 — Safety grading (done)
- [x] Merged safety checks into `grimoire_safety.py` (originals untouched).
- [x] Read-only bus scan, secret masking, Ba/Ka SHIP-or-KILL gate.
- [x] Optional Gemini review (off by default).

## Phase 2 — Simulated panel (done)
- [x] Trilateral panel on Gemini and Groq (`simulate_panel.py`).
- [x] Parallel proponent/opponent debate with neutral judge.
- [x] Judge fences untrusted text in `<data>` tags.

## Phase 3 — Verification tooling (in progress)
- [x] `larp_scan.py`: assertion-free tests, trivial assertions, claims without receipts.
- [x] Judge injection red-team (`tests/test_judge_redteam.py`).
- [x] Score the judge on a labeled known-good / known-bad set (6/6, `eval/`).
- [x] Judge prompt separates artifact assertions from agreement; side prompts fence the artifact.
- [~] Broader judge eval: 6 items is a baseline, not a benchmark. Labels are agent-authored.
- [x] `larp_scan` on the home repo: 2 real holes found and fixed upstream; 12 claim
  findings remain as review items.

## Phase 4 — Usability (not started)
- [ ] Decide the delivery surface for non-terminal users (MRD item 5).
- [ ] Decide whether the judge takes user-tunable config (MRD item 4).

## Not doing (yet)
- No live-service tests in the suite. Tests stay offline and deterministic.
- No repo-wide smell gate; scope stays on changed code.
- [x] Local web UI moved to `~/grim-oracle` (own repo: server, page, cannibal mode).
