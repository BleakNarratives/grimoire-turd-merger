#!/usr/bin/env python3
"""simulate_panel — v0 trilateral panel over one text artifact.

Three fixed perspectives react to the same text:
  skeptic      what sounds false, unsupported, or breakable
  target_user  would someone in this audience use or pay for it
  balancer     where the first two disagree, and what evidence would settle it

Every reaction is SIMULATED model output, not measured human response.
Stdlib only. --dry-run prints the prompts and makes no network call.
Model calls reuse the Gemini path in grimoire_safety (secrets redacted first).
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

PERSPECTIVES = {
    "skeptic": (
        "You are a skeptical reviewer. List the claims in the artifact that are "
        "unsupported, vague, or likely false. Quote each claim. Do not invent facts."
    ),
    "target_user": (
        "You are a member of the audience described below. Say whether you would "
        "use or pay for this, what you would expect it to do, and what would stop "
        "you. Speak only from that audience's likely view."
    ),
    "balancer": (
        "You receive two reviews of the same artifact. State where they disagree, "
        "which disagreements matter most, and what concrete evidence would settle "
        "each one. Do not pick a winner without evidence."
    ),
}

LABEL = "SIMULATED — model reaction, not a measured human response."


def build_prompt(name: str, artifact: str, audience: str, prior: dict[str, str]) -> str:
    """Compose the prompt for one perspective. Pure; no I/O."""
    parts = [PERSPECTIVES[name], ""]
    if audience:
        parts += [f"Audience / region: {audience}", ""]
    parts += ["ARTIFACT:", artifact.strip(), ""]
    for other, text in prior.items():
        parts += [f"PRIOR REVIEW ({other}):", text.strip(), ""]
    parts.append("Keep the answer under 250 words. Plain text, no preamble.")
    return "\n".join(parts)


def render_report(results: dict[str, str], audience: str) -> str:
    """Format the three reactions with the simulated label on every section."""
    lines = [LABEL, ""]
    if audience:
        lines += [f"Audience / region: {audience}", ""]
    for name in PERSPECTIVES:
        lines += [f"== {name.upper()} ==", results.get(name, "(no output)").strip(), ""]
    return "\n".join(lines).rstrip() + "\n"


def run_panel(artifact: str, audience: str, ask) -> dict[str, str]:
    """Run perspectives in order; balancer sees the first two. `ask(prompt) -> str`."""
    results: dict[str, str] = {}
    for name in ("skeptic", "target_user"):
        results[name] = ask(build_prompt(name, artifact, audience, {}))
    results["balancer"] = ask(build_prompt("balancer", artifact, audience,
                                           {"skeptic": results["skeptic"],
                                            "target_user": results["target_user"]}))
    return results


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Simulated trilateral panel over one text file.")
    ap.add_argument("artifact", help="text file to review (pitch, README, copy)")
    ap.add_argument("--audience", default="", help="demographic or region note")
    ap.add_argument("--dry-run", action="store_true", help="print prompts; no model call")
    ap.add_argument("--provider", choices=["gemini", "groq"], default="gemini")
    ap.add_argument("--model", default="", help="override the provider's default model")
    a = ap.parse_args(argv)
    p = Path(a.artifact).expanduser()
    if not p.is_file():
        print(f"simulate_panel: not a file: {p}", file=sys.stderr)
        return 2
    artifact = p.read_text(encoding="utf-8", errors="replace")
    if a.dry_run:
        for name in PERSPECTIVES:
            print(f"----- {name} (first pass prompt; balancer also gets prior reviews) -----")
            print(build_prompt(name, artifact, a.audience, {}))
            print()
        return 0
    import grimoire_safety as gs
    text, n = gs.redact_text(artifact)
    if n:
        print(f"simulate_panel: redacted {n} secret-shaped match(es) before send", file=sys.stderr)

    def ask(prompt: str) -> str:
        if a.provider == "groq":
            return gs.groq_text(prompt, a.model or "openai/gpt-oss-120b")
        return gs.gemini_text(prompt, a.model or "gemini-3.1-flash-lite")

    try:
        results = run_panel(text, a.audience, ask)
    except RuntimeError as e:
        print(f"simulate_panel: {e}", file=sys.stderr)
        return 2
    print(render_report(results, a.audience), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
