#!/usr/bin/env python3
"""grimoire_tui — read-only curses console for the Turd Merger results.

Views (Tab to cycle):  BUS  ·  ROADMAP  ·  ABOUT
Keys: j/k or arrows move · Tab switch view · r reload · q quit
Stdlib only. Never writes. Reads .grimoire/bus and the roadmap index.
"""
from __future__ import annotations
import curses
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import grimoire_safety as gs  # noqa: E402
import roadmap_map as rm      # noqa: E402

BUS_DIR = Path.home() / ".grimoire" / "bus"
ROOT = Path.cwd()
VIEWS = ("BUS", "ROADMAP", "ABOUT")

# palette: pair ids
C_TITLE, C_OK, C_WARN, C_FLAG, C_DIM, C_ACCENT, C_SEL = 1, 2, 3, 4, 5, 6, 7


def load_bus() -> list[dict]:
    if not BUS_DIR.is_dir():
        return []
    files = sorted(BUS_DIR.glob("*.bus")) + sorted(BUS_DIR.glob("*.json"))
    return [gs.grade_file(f) for f in files]


def load_roadmaps() -> list[dict]:
    return [rm.parse_roadmap(p, ROOT) for p in rm.find_roadmaps(ROOT)]


def init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(C_TITLE, curses.COLOR_MAGENTA, -1)
    curses.init_pair(C_OK, curses.COLOR_GREEN, -1)
    curses.init_pair(C_WARN, curses.COLOR_YELLOW, -1)
    curses.init_pair(C_FLAG, curses.COLOR_RED, -1)
    curses.init_pair(C_DIM, curses.COLOR_WHITE, -1)
    curses.init_pair(C_ACCENT, curses.COLOR_CYAN, -1)
    curses.init_pair(C_SEL, curses.COLOR_BLACK, curses.COLOR_CYAN)


def safe_add(win, y: int, x: int, text: str, attr: int = 0) -> None:
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    try:
        win.addnstr(y, x, text, max(0, w - x - 1), attr)
    except curses.error:
        pass


def draw_header(win, view_idx: int) -> None:
    h, w = win.getmaxyx()
    title = " GRIMOIRE · TURD MERGER "
    safe_add(win, 0, 0, "─" * w, curses.color_pair(C_DIM))
    safe_add(win, 0, 2, title, curses.color_pair(C_TITLE) | curses.A_BOLD)
    x = 2 + len(title) + 2
    for i, v in enumerate(VIEWS):
        label = f" {v} "
        attr = curses.color_pair(C_SEL) | curses.A_BOLD if i == view_idx else curses.color_pair(C_DIM)
        safe_add(win, 0, x, label, attr)
        x += len(label) + 1


def draw_footer(win, msg: str) -> None:
    h, w = win.getmaxyx()
    keys = " j/k move · Tab view · r reload · q quit "
    safe_add(win, h - 1, 0, keys.ljust(w - 1)[: w - 1], curses.color_pair(C_SEL))
    if msg:
        safe_add(win, h - 2, 2, msg, curses.color_pair(C_ACCENT))


def bus_row(r: dict) -> tuple[str, int]:
    status = r.get("status", "SKIP")
    attr = {"OK": C_OK, "WARN": C_WARN, "FLAG": C_FLAG}.get(status, C_DIM)
    name = Path(r.get("file", "?")).name
    score = r.get("score", "-")
    return f"{status:<5} {str(score):>5}  {name}", attr


def draw_bus(win, rows: list[dict], sel: int, top: int) -> None:
    h, w = win.getmaxyx()
    if not rows:
        safe_add(win, 3, 4, "bus empty — nothing to grade yet.", curses.color_pair(C_DIM))
        return
    list_h = h - 6
    for i in range(list_h):
        idx = top + i
        if idx >= len(rows):
            break
        text, attr = bus_row(rows[idx])
        line = f"  {text}"
        if idx == sel:
            safe_add(win, 2 + i, 0, line.ljust(w - 1), curses.color_pair(C_SEL) | curses.A_BOLD)
        else:
            safe_add(win, 2 + i, 0, line, curses.color_pair(attr))
    # detail pane
    if 0 <= sel < len(rows):
        r = rows[sel]
        y = h - 4
        safe_add(win, y, 2, f"receipt: {'yes' if r.get('receipt') else 'no'}   sha256: {r.get('sha256', '-')}",
                 curses.color_pair(C_DIM))
        for j, f in enumerate(r.get("findings", [])[:2]):
            safe_add(win, y + 1 + j, 2, f"{f['source']}:{f['pattern']} x{f['hits']}",
                     curses.color_pair(C_WARN))


def draw_roadmap(win, items: list[dict], sel: int, top: int) -> None:
    h, w = win.getmaxyx()
    if not items:
        safe_add(win, 3, 4, "no roadmaps found under this root.", curses.color_pair(C_DIM))
        return
    list_h = h - 6
    for i in range(list_h):
        idx = top + i
        if idx >= len(items):
            break
        it = items[idx]
        pct = f"{it['done']}/{it['total']}" if it.get("total") else "  -  "
        line = f"  {pct:>7}  {it.get('path', '?')}"
        attr = curses.color_pair(C_OK) if it.get("total") and it["done"] == it["total"] else curses.color_pair(C_DIM)
        if idx == sel:
            safe_add(win, 2 + i, 0, line.ljust(w - 1), curses.color_pair(C_SEL) | curses.A_BOLD)
        else:
            safe_add(win, 2 + i, 0, line, attr)
    if 0 <= sel < len(items):
        it = items[sel]
        y = h - 4
        safe_add(win, y, 2, it.get("title", ""), curses.color_pair(C_ACCENT))
        for j, s in enumerate(it.get("signals", [])[:2]):
            safe_add(win, y + 1 + j, 2, s, curses.color_pair(C_DIM))


def draw_about(win) -> None:
    lines = [
        ("GRIMOIRE · Turd Merger", curses.color_pair(C_TITLE) | curses.A_BOLD),
        ("", 0),
        ("Read-only. Stdlib only. No network unless you run  grimoire_safety llm.", curses.color_pair(C_DIM)),
        ("Verdicts: OK / WARN / FLAG  ·  SHIP / HOLD / KILL", curses.color_pair(C_ACCENT)),
        ("Rule: claim without receipt is a flag, not proof.", curses.color_pair(C_WARN)),
    ]
    for i, (t, a) in enumerate(lines):
        safe_add(win, 3 + i, 4, t, a)


def main_loop(stdscr) -> None:
    curses.curs_set(0)
    init_colors()
    stdscr.keypad(True)
    view = 0
    sel = {"BUS": 0, "ROADMAP": 0}
    top = {"BUS": 0, "ROADMAP": 0}
    data = {"BUS": load_bus(), "ROADMAP": load_roadmaps()}
    msg = ""
    while True:
        stdscr.erase()
        draw_header(stdscr, view)
        name = VIEWS[view]
        if name == "BUS":
            rows = data["BUS"]
            draw_bus(stdscr, rows, sel["BUS"], top["BUS"])
        elif name == "ROADMAP":
            draw_roadmap(stdscr, data["ROADMAP"], sel["ROADMAP"], top["ROADMAP"])
        else:
            draw_about(stdscr)
        draw_footer(stdscr, msg)
        stdscr.refresh()
        msg = ""
        key = stdscr.getch()
        if key in (ord("q"), 27):
            return
        if key == 9:  # Tab
            view = (view + 1) % len(VIEWS)
        elif key == ord("r"):
            data = {"BUS": load_bus(), "ROADMAP": load_roadmaps()}
            msg = "reloaded"
        elif name in sel and key in (ord("j"), curses.KEY_DOWN):
            n = len(data[name])
            if n:
                sel[name] = min(sel[name] + 1, n - 1)
        elif name in sel and key in (ord("k"), curses.KEY_UP):
            sel[name] = max(sel[name] - 1, 0)
        if name in sel:
            page = max(stdscr.getmaxyx()[0] - 6, 1)
            if sel[name] < top[name]:
                top[name] = sel[name]
            elif sel[name] >= top[name] + page:
                top[name] = sel[name] - page + 1


def main() -> int:
    if not sys.stdout.isatty():
        print("grimoire_tui: needs an interactive terminal", file=sys.stderr)
        return 2
    curses.wrapper(main_loop)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
