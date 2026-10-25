#!/usr/bin/env python3
"""demo_svg — render an animated SVG of the Turd Merger results.

Pure SMIL animation: no JavaScript, so it plays in GitHub READMEs and browsers.
Stdlib only. Reads real bus grades and roadmap counts; writes one SVG file.

Usage:
  python3 demo_svg.py --bus-dir ~/.grimoire/bus --root . -o demo.svg
"""
from __future__ import annotations
import argparse
import html
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import grimoire_safety as gs  # noqa: E402
import roadmap_map as rm      # noqa: E402

COLORS = {"OK": "#3ddc97", "WARN": "#f5c542", "FLAG": "#ff5c7a", "SKIP": "#7a8699"}
BG, FG, ACCENT = "#0b0f1a", "#e6edf7", "#7c5cff"


def collect(bus_dir: Path, root: Path) -> tuple[list[dict], list[dict]]:
    bus = []
    if bus_dir.is_dir():
        files = sorted(bus_dir.glob("*.bus")) + sorted(bus_dir.glob("*.json"))
        bus = [gs.grade_file(f) for f in files]
    roads = [rm.parse_roadmap(p, root) for p in rm.find_roadmaps(root)]
    return bus, roads


def render(bus: list[dict], roads: list[dict]) -> str:
    width, row_h = 760, 30
    counts = {k: sum(1 for r in bus if r.get("status") == k) for k in COLORS}
    total_done = sum(r.get("done", 0) for r in roads)
    total_boxes = sum(r.get("total", 0) for r in roads)
    height = 170 + row_h * max(len(bus), 1) + 40
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="monospace">',
        f'<rect width="100%" height="100%" rx="14" fill="{BG}"/>',
        f'<text x="24" y="40" fill="{ACCENT}" font-size="20" font-weight="bold">'
        f'GRIMOIRE · TURD MERGER</text>',
        f'<text x="24" y="62" fill="{FG}" font-size="12">'
        f'{len(bus)} bus entries graded · {counts["FLAG"]} flagged · '
        f'{total_done}/{total_boxes} roadmap checkboxes done</text>',
    ]
    # animated bar: width grows from 0 to the real flagged share
    flagged_share = (counts["FLAG"] / len(bus)) if bus else 0.0
    bar_w = round(700 * flagged_share, 1)
    parts += [
        f'<rect x="24" y="80" width="700" height="10" rx="5" fill="#1b2336"/>',
        f'<rect x="24" y="80" width="0" height="10" rx="5" fill="{COLORS["FLAG"]}">'
        f'<animate attributeName="width" from="0" to="{bar_w}" dur="1.2s" fill="freeze"/>'
        f'</rect>',
    ]
    y = 120
    for i, r in enumerate(bus):
        status = r.get("status", "SKIP")
        color = COLORS.get(status, COLORS["SKIP"])
        name = html.escape(Path(r.get("file", "?")).name)[:60]
        score = r.get("score", "-")
        delay = f"{0.2 + i * 0.15:.2f}s"
        parts += [
            f'<g opacity="0">',
            f'<animate attributeName="opacity" from="0" to="1" begin="{delay}" dur="0.4s" fill="freeze"/>',
            f'<circle cx="34" cy="{y - 5}" r="6" fill="{color}"/>',
            f'<text x="50" y="{y}" fill="{FG}" font-size="13">'
            f'<tspan fill="{color}" font-weight="bold">{status:<4}</tspan>  '
            f'{score}  {name}</text>',
            f'</g>',
        ]
        y += row_h
    if not bus:
        parts.append(f'<text x="24" y="{y}" fill="{FG}" font-size="13">bus is empty — nothing graded yet.</text>')
    footer_y = height - 16
    parts += [
        f'<text x="24" y="{footer_y}" fill="#7a8699" font-size="11">'
        f'read-only · stdlib · claim without receipt = flag, not proof</text>',
        "</svg>",
    ]
    return "\n".join(parts) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render animated SVG of merger results.")
    ap.add_argument("--bus-dir", default="~/.grimoire/bus")
    ap.add_argument("--root", default=".")
    ap.add_argument("-o", "--output", default="demo.svg")
    a = ap.parse_args(argv)
    bus, roads = collect(Path(a.bus_dir).expanduser(), Path(a.root).expanduser().resolve())
    out = Path(a.output).expanduser()
    out.write_text(render(bus, roads), encoding="utf-8")
    print(f"wrote {out} ({len(bus)} bus, {len(roads)} roadmaps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
