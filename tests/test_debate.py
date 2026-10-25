"""Deterministic tests for the parallel debate mode: no network, fake ask function."""
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import simulate_panel as sp  # noqa: E402


class DebatePromptTests(unittest.TestCase):
    def test_sides_have_opposite_roles(self):
        pro = sp.build_debate_prompt("proponent", "x", "")
        con = sp.build_debate_prompt("opponent", "x", "")
        self.assertIn("FOR", pro)
        self.assertIn("AGAINST", con)
        self.assertNotEqual(pro, con)

    def test_judge_sees_both_sides(self):
        p = sp.build_judge_prompt("x", "PRO-ARG", "CON-ARG")
        self.assertIn("PRO-ARG", p)
        self.assertIn("CON-ARG", p)
        self.assertIn("neutral judge", p)

    def test_audience_only_when_given(self):
        self.assertIn("Audience / region: EU", sp.build_debate_prompt("opponent", "x", "EU"))
        self.assertNotIn("Audience / region", sp.build_debate_prompt("opponent", "x", ""))


class DebateRunTests(unittest.TestCase):
    def test_proponent_and_opponent_run_concurrently(self):
        # Both sides must be in flight at once: each waits on a barrier of 2.
        barrier = threading.Barrier(2, timeout=5)
        seen = []
        lock = threading.Lock()

        def fake(prompt):
            if "FOR" in prompt or "AGAINST" in prompt:
                barrier.wait()  # deadlocks/raises if the calls were sequential
                with lock:
                    seen.append(prompt)
                return "side"
            return "judged"

        out = sp.run_debate("artifact", "", fake)
        self.assertEqual(len(seen), 2)
        self.assertEqual(out["judge"], "judged")

    def test_judge_runs_after_both_sides(self):
        calls = []

        def fake(prompt):
            calls.append("judge" if "neutral judge" in prompt else "side")
            return "text"

        sp.run_debate("artifact", "", fake)
        self.assertEqual(calls[-1], "judge")
        self.assertEqual(calls.count("side"), 2)

    def test_judge_receives_both_side_outputs(self):
        def fake(prompt):
            if "neutral judge" in prompt:
                return "judged"
            return "PRO-OUT" if "FOR" in prompt else "CON-OUT"

        out = sp.run_debate("artifact", "", fake)
        self.assertEqual(out["proponent"], "PRO-OUT")
        self.assertEqual(out["opponent"], "CON-OUT")


class DebateReportTests(unittest.TestCase):
    def test_debate_report_is_labeled_simulated(self):
        r = sp.render_debate({"proponent": "a", "opponent": "b", "judge": "c"}, "")
        self.assertTrue(r.startswith(sp.LABEL))
        self.assertIn("== JUDGE ==", r)


if __name__ == "__main__":
    unittest.main()
