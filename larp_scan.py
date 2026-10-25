#!/usr/bin/env python3
"""larp_scan.py -- code-level larp detector. Stdlib only, read-only.

grimoire_safety grades prose (bus entries, transcripts). This grades code:

  assertion-free-test   a test_* function that never asserts or fails
  trivial-assertion     assertTrue(True), assert True, assertEqual(x, x)
  claim-without-receipt a completion claim (see FLAG_REGEX in grimoire_safety)
                        in a docstring or comment with no receipt beside it

A receipt is the same concrete shape grimoire_safety.has_receipt accepts.
Prose announcing a result does not count as evidence.

Heuristic, not proof. A passing AST check does not show a test is right; it
shows the test is capable of failing. Findings are for review, not a verdict.

Usage:  python3 larp_scan.py [ROOT ...] [--strict]
Exit 0 normally; with --strict, exit 1 if any finding is reported.
"""
from __future__ import annotations

import ast
import io
import sys
import tokenize
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grimoire_safety import FLAG_REGEX, has_receipt  # noqa: E402

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
ASSERT_CALL_PREFIXES = ("assert", "fail")  # self.assertX, self.fail, pytest-style helpers
ASSERT_CALL_NAMES = {"raises", "warns", "fail", "exit"}  # pytest.raises, sys.exit-style checks


def iter_py(roots):
    for root in roots:
        root = Path(root)
        files = [root] if root.is_file() else root.rglob("*.py")
        for p in files:
            if not any(part in SKIP_DIRS for part in p.parts):
                yield p


def _is_assert_call(node: ast.Call) -> bool:
    fn = node.func
    name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
    return name.startswith(ASSERT_CALL_PREFIXES) or name in ASSERT_CALL_NAMES


def _is_trivial(node: ast.AST) -> bool:
    if isinstance(node, ast.Assert):
        t = node.test
        return isinstance(t, ast.Constant) and bool(t.value) is True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        name = node.func.attr
        args = node.args
        if name == "assertTrue" and args and isinstance(args[0], ast.Constant) and args[0].value is True:
            return True
        if name in ("assertEqual", "assertIs") and len(args) >= 2:
            a, b = args[0], args[1]
            # Only literal or plain-name operands are provably self-equal. A call on
            # both sides (f(7) == f(7)) is a determinism check, not a tautology.
            if ast.dump(a) == ast.dump(b) and isinstance(a, (ast.Constant, ast.Name, ast.Attribute)):
                return True
    return False


def _local_helpers(tree: ast.AST) -> dict[str, ast.AST]:
    return {n.name: n for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _asserts(fn: ast.AST, helpers: dict[str, ast.AST], seen: set[str]) -> bool:
    """True if fn asserts directly or calls a same-file helper that does.

    Follows same-file helpers only; an assertion in another module is not seen.
    """
    for node in ast.walk(fn):
        if isinstance(node, ast.Assert):
            return True
        if isinstance(node, ast.Call):
            if _is_assert_call(node):
                return True
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if name in helpers and name not in seen:
                seen.add(name)
                if _asserts(helpers[name], helpers, seen):
                    return True
    return False


def check_tests(tree: ast.AST, rel: str) -> list[dict]:
    out = []
    helpers = _local_helpers(tree)
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not fn.name.startswith("test"):
            continue
        has_assert = _asserts(fn, helpers, set())
        for node in ast.walk(fn):
            if _is_trivial(node):
                out.append({"file": rel, "line": node.lineno, "kind": "trivial-assertion",
                            "detail": f"in {fn.name}(): assertion can never fail"})
        if not has_assert:
            out.append({"file": rel, "line": fn.lineno, "kind": "assertion-free-test",
                        "detail": f"{fn.name}() never asserts or fails"})
    return out


def _claim_texts(tree: ast.AST, source: str):
    """Yield (line, text) for every docstring and every comment."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                line = getattr(node, "lineno", 1)
                yield line, doc
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.COMMENT:
            yield tok.start[0], tok.string


def check_claims(source: str, tree: ast.AST, rel: str) -> list[dict]:
    out = []
    for line, text in _claim_texts(tree, source):
        if FLAG_REGEX.search(text) and not has_receipt(text):
            snippet = " ".join(text.split())[:70]
            out.append({"file": rel, "line": line, "kind": "claim-without-receipt",
                        "detail": snippet})
    return out


def scan_file(path: Path, base: Path) -> list[dict]:
    rel = str(path.relative_to(base)) if path.is_relative_to(base) else str(path)
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=rel)
    except (SyntaxError, ValueError) as e:
        return [{"file": rel, "line": 0, "kind": "unparseable", "detail": str(e)[:70]}]
    findings = []
    if path.name.startswith("test_") or path.parent.name == "tests":
        findings += check_tests(tree, rel)
    findings += check_claims(source, tree, rel)
    return findings


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    strict = "--strict" in args
    roots = [a for a in args if a != "--strict"] or ["."]
    base = Path(roots[0]).resolve() if Path(roots[0]).is_dir() else Path(roots[0]).resolve().parent
    findings = []
    for p in iter_py(roots):
        findings += scan_file(p.resolve(), base)
    for f in findings:
        print(f"{f['file']}:{f['line']}  {f['kind']}  {f['detail']}")
    print(f"larp_scan: {len(findings)} finding(s) in {len(roots)} root(s)")
    return 1 if (strict and findings) else 0


if __name__ == "__main__":
    sys.exit(main())
