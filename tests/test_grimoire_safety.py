"""Deterministic tests: temp dirs only, no network, no real credentials."""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import grimoire_safety as gs  # noqa: E402
import roadmap_map as rm      # noqa: E402

FAKE_GH = "ghp_" + "A" * 36  # synthetic, not a real token


class ScoringTests(unittest.TestCase):
    def test_clean_text_scores_one(self):
        score, findings = gs.score_text("Read config.json. Listening on port 8080.")
        self.assertEqual(score, 1.0)
        self.assertEqual(findings, [])

    def test_unverified_claim_is_penalised(self):
        score, findings = gs.score_text("All tests passed. Everything is done.")
        self.assertLess(score, 1.0)
        self.assertTrue(any(f["source"] == "tribunal-flagger" for f in findings))

    def test_fabricated_count_pattern(self):
        score, findings = gs.score_text("all 12 tests passed")
        self.assertTrue(any(f["pattern"] == "fabricated_count" for f in findings))
        self.assertLessEqual(score, 0.5)

    def test_score_never_negative(self):
        score, _ = gs.score_text("done " * 200 + "guaranteed " * 50)
        self.assertGreaterEqual(score, 0.0)


class ReceiptTests(unittest.TestCase):
    def test_exit_zero_is_a_receipt(self):
        self.assertTrue(gs.has_receipt("$ pytest\nexit: 0"))

    def test_bare_claim_has_no_receipt(self):
        self.assertFalse(gs.has_receipt("Everything is done, trust me."))


class RedactionTests(unittest.TestCase):
    def test_secret_is_masked_not_echoed(self):
        clean, n = gs.redact_text(f"token={FAKE_GH}")
        self.assertEqual(n, 1)
        self.assertNotIn(FAKE_GH, clean)
        self.assertIn("[REDACTED:github-token:", clean)

    def test_preview_never_contains_full_secret(self):
        hits = gs.check_secrets(FAKE_GH)
        self.assertTrue(hits)
        self.assertNotIn(FAKE_GH, hits[0]["preview"])

    def test_clean_text_unchanged(self):
        clean, n = gs.redact_text("nothing sensitive here")
        self.assertEqual((clean, n), ("nothing sensitive here", 0))


class FileGradingTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_flagged_bus_file(self):
        p = self.dir / "bad.bus"
        p.write_text("All tests passed. Done, verified. Everything is done.")
        r = gs.grade_file(p, threshold=0.6)
        self.assertEqual(r["status"], "FLAG")
        self.assertFalse(r["receipt"])

    def test_clean_bus_file_is_ok(self):
        p = self.dir / "ok.bus"
        p.write_text("Read config.json\nListening on port 8080")
        self.assertEqual(gs.grade_file(p)["status"], "OK")

    def test_missing_file_is_skipped_not_crashed(self):
        r = gs.grade_file(self.dir / "nope.bus")
        self.assertEqual(r["status"], "SKIP")


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, name, body):
        p = self.dir / name
        p.write_text(body)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = gs.cmd_validate(type("A", (), {"target": str(p)})())
        return code, buf.getvalue()

    def test_ship_declaration_passes(self):
        body = ("name: x\nversion: 1\nintent: y\nsuccess_criteria: z\n"
                "scope: {in: a, out: b, boundaries: c}\nmetadata:\n  status: ship\n")
        code, out = self._run("ok.ba.yaml", body)
        self.assertEqual(code, 0)
        self.assertIn("PASS", out)

    def test_hold_is_refused(self):
        body = "name: x\nmetadata:\n  status: hold\n"
        code, out = self._run("hold.ba.yaml", body)
        self.assertEqual(code, 1)
        self.assertIn("HOLD", out)


class RoadmapTests(unittest.TestCase):
    def test_checkbox_counting(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rp = root / "ROADMAP.md"
            rp.write_text("# Plan\n- [x] one\n- [ ] two\n- [X] three\n")
            item = rm.parse_roadmap(rp, root)
            self.assertEqual((item["done"], item["total"]), (2, 3))

    def test_find_skips_recovery_trees(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "keep").mkdir()
            (root / "keep" / "ROADMAP.md").write_text("# k")
            (root / "turd-merger-capture").mkdir()
            (root / "turd-merger-capture" / "ROADMAP.md").write_text("# skip")
            found = [p.relative_to(root).as_posix() for p in rm.find_roadmaps(root)]
            self.assertEqual(found, ["keep/ROADMAP.md"])


class LlmPathTests(unittest.TestCase):
    def test_no_key_sends_nothing(self):
        import os
        saved = os.environ.pop("GEMINI_API_KEY", None)
        try:
            with tempfile.TemporaryDirectory() as d:
                p = Path(d) / "t.txt"
                p.write_text("hello")
                real_vault = gs.VAULT
                gs.VAULT = Path(d) / "missing.json"  # no vault, no key
                try:
                    code = gs.cmd_llm(type("A", (), {"target": str(p), "image": None,
                                                   "prompt": "x", "model": "m"})())
                finally:
                    gs.VAULT = real_vault
            self.assertEqual(code, 2)
        finally:
            if saved is not None:
                os.environ["GEMINI_API_KEY"] = saved


class TuiHelperTests(unittest.TestCase):
    def test_bus_row_maps_status_to_color(self):
        import grimoire_tui as t
        text, attr = t.bus_row({"status": "FLAG", "score": 0.0, "file": "/x/a.bus"})
        self.assertIn("FLAG", text)
        self.assertEqual(attr, t.C_FLAG)

    def test_bus_row_unknown_status_is_dim(self):
        import grimoire_tui as t
        _, attr = t.bus_row({"status": "SKIP", "file": "/x/a"})
        self.assertEqual(attr, t.C_DIM)

    def test_summarize_bus(self):
        import grimoire_tui as t
        rows = [
            {"status": "OK"},
            {"status": "WARN"},
            {"status": "FLAG"},
            {"status": "OK"},
            {"status": "UNKNOWN"},
        ]
        s = t.summarize_bus(rows)
        self.assertEqual(s["OK"], 2)
        self.assertEqual(s["WARN"], 1)
        self.assertEqual(s["FLAG"], 1)
        self.assertEqual(s["SKIP"], 1)
        self.assertEqual(s["total"], 5)

    def test_summarize_roadmap(self):
        import grimoire_tui as t
        items = [
            {"done": 3, "total": 3},
            {"done": 1, "total": 4},
        ]
        s = t.summarize_roadmap(items)
        self.assertEqual(s["roadmaps"], 2)
        self.assertEqual(s["done"], 4)
        self.assertEqual(s["total"], 7)
        self.assertEqual(s["completed_roadmaps"], 1)

    def test_format_status_line(self):
        import grimoire_tui as t
        rows = [{"status": "OK"}, {"status": "FLAG"}]
        st_bus = t.format_status_line("BUS", rows, 0)
        self.assertIn("BUS: 2 entries", st_bus)
        self.assertIn("1 OK", st_bus)
        self.assertIn("1 FLAG", st_bus)
        self.assertIn("#1/2", st_bus)

        empty_bus = t.format_status_line("BUS", [], 0)
        self.assertEqual(empty_bus, "BUS: 0 entries")

        maps = [{"done": 2, "total": 4}]
        st_rm = t.format_status_line("ROADMAP", maps, 0)
        self.assertIn("ROADMAP: 1 maps", st_rm)
        self.assertIn("2/4 tasks · 50%", st_rm)

        st_about = t.format_status_line("ABOUT", [], 0)
        self.assertIn("ABOUT", st_about)

    def test_format_empty_state(self):
        import grimoire_tui as t
        lines_bus = t.format_empty_state("BUS")
        self.assertTrue(any("Empty Bus" in line for line in lines_bus))
        lines_rm = t.format_empty_state("ROADMAP")
        self.assertTrue(any("No Roadmaps Found" in line for line in lines_rm))

    def test_format_keyhints(self):
        import grimoire_tui as t
        self.assertIn("j/k move", t.format_keyhints(80))
        self.assertIn("j/k:move", t.format_keyhints(40))
        self.assertEqual(t.format_keyhints(20), " j/k Tab r q ")

    def test_compute_layout_normal_and_small(self):
        import grimoire_tui as t
        norm = t.compute_layout(24, 80)
        self.assertEqual(norm["header_y"], 0)
        self.assertEqual(norm["status_y"], 1)
        self.assertEqual(norm["detail_h"], 3)
        self.assertEqual(norm["footer_y"], 23)
        self.assertGreater(norm["list_h"], 0)

        small = t.compute_layout(5, 40)
        self.assertEqual(small["header_y"], 0)
        self.assertEqual(small["status_y"], -1)
        self.assertEqual(small["detail_h"], 0)
        self.assertEqual(small["footer_y"], 4)


if __name__ == "__main__":
    unittest.main()
