"""Deterministic tests for simulate_panel: no network, fake ask function."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import simulate_panel as sp  # noqa: E402


class PromptTests(unittest.TestCase):
    def test_each_perspective_has_its_role(self):
        for name in sp.PERSPECTIVES:
            p = sp.build_prompt(name, "x", "", {})
            self.assertIn(sp.PERSPECTIVES[name], p)

    def test_audience_line_only_when_given(self):
        with_aud = sp.build_prompt("skeptic", "x", "US devs", {})
        without = sp.build_prompt("skeptic", "x", "", {})
        self.assertIn("Audience / region: US devs", with_aud)
        self.assertNotIn("Audience / region", without)

    def test_balancer_sees_both_prior_reviews(self):
        p = sp.build_prompt("balancer", "x", "", {"skeptic": "SKEP-TEXT",
                                                  "target_user": "USER-TEXT"})
        self.assertIn("SKEP-TEXT", p)
        self.assertIn("USER-TEXT", p)


class RunTests(unittest.TestCase):
    def test_run_order_and_balancer_inputs(self):
        calls = []

        def fake(prompt):
            calls.append(prompt)
            return f"reply{len(calls)}"

        out = sp.run_panel("artifact", "", fake)
        self.assertEqual(len(calls), 3)
        self.assertEqual(out["skeptic"], "reply1")
        self.assertEqual(out["target_user"], "reply2")
        self.assertEqual(out["balancer"], "reply3")
        self.assertIn("reply1", calls[2])
        self.assertIn("reply2", calls[2])


class ReportTests(unittest.TestCase):
    def test_every_report_is_labeled_simulated(self):
        report = sp.render_report({"skeptic": "a", "target_user": "b", "balancer": "c"}, "")
        self.assertTrue(report.startswith(sp.LABEL))
        self.assertIn("SIMULATED", report)

    def test_missing_perspective_is_marked(self):
        report = sp.render_report({"skeptic": "a"}, "")
        self.assertIn("(no output)", report)


if __name__ == "__main__":
    unittest.main()
