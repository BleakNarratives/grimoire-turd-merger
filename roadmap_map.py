#!/usr/bin/env python3
"""roadmap_map — index all ROADMAP.md files into one stick-on-the-wall map.

Stdlib only. Read-only (writes only the index file you name with -o).

Usage:
  python3 turd-merger-tools/roadmap_map.py [--root .] [-o turd-merger-tools/ROADMAP_INDEX.md]
  python3 turd-merger-tools/roadmap_map.py --root . --json
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".cache"}


def find_roadmaps(root: Path) -> list[Path]:
    out = []
    for p in root.rglob("ROADMAP*.md"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        # skip massive recovery trees + merger captures to stay lean (no double-count)
        if any(part in ("UNPACKED", "NAT-Recovery-Kernel", "MikeySwarm", "turd-merger-capture", "recovery_staged", "recovery_staging") for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def parse_roadmap(p: Path, root: Path) -> dict:
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"path": str(p), "error": "unreadable"}
    lines = text.splitlines()
    title = lines[0].strip("# ").strip() if lines else p.name
    checkboxes = re.findall(r"^\s*-\s*\[( |x|X)\]", text, re.M)
    done = sum(1 for c in checkboxes if c.lower() == "x")
    total = len(checkboxes)
    phases = re.findall(r"^#{1,3}\s*(.+)", text, re.M)[:10]
    # first P0/P1 line as signal
    prio = []
    for ln in lines:
        if re.search(r"\bP0\b|\bP1\b|Phase\s+\d", ln):
            prio.append(ln.strip()[:120])
            if len(prio) >= 5:
                break
    return {"path": str(p.relative_to(root) if p.is_absolute() else p),
            "title": title[:120], "done": done, "total": total,
            "phases": [x.strip()[:100] for x in phases], "signals": prio,
            "lines": len(lines)}


def render_index(items: list[dict], root: Path) -> str:
    L = ["# ROADMAP INDEX — auto-map (turd-merger-tools/roadmap_map.py)",
         f"# root: {root} | files: {len(items)}",
         "# Regen: python3 turd-merger-tools/roadmap_map.py --root . -o turd-merger-tools/ROADMAP_INDEX.md",
         ""]
    done_t = sum(i.get("done", 0) for i in items)
    tot_t = sum(i.get("total", 0) for i in items)
    L.append(f"## Totals: {done_t}/{tot_t} checkboxes done across {len(items)} roadmap files")
    L.append("")
    L.append("## Map (where to look first)")
    for i in items:
        pct = f"{i['done']}/{i['total']}" if i.get("total") else "no-boxes"
        L.append(f"- `{i['path']}` — {i.get('title','')} [{pct}]")
        for s in i.get("signals", [])[:3]:
            L.append(f"  - {s}")
    L.append("")
    L.append("## Next smallest actions (from P0/Phase signals)")
    n = 0
    for i in items:
        for s in i.get("signals", []):
            if n >= 10:
                break
            L.append(f"- [{i['path']}] {s}")
            n += 1
    L.append("")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("-o", "--output", default="")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root).expanduser().resolve()
    items = [parse_roadmap(p, root) for p in find_roadmaps(root)]
    if a.json:
        print(json.dumps(items, indent=2))
        return 0
    out = render_index(items, root)
    if a.output:
        Path(a.output).expanduser().write_text(out + "\n", encoding="utf-8")
        print(f"wrote {a.output} ({len(items)} roadmaps)")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
