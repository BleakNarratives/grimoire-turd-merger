"""Tests for larp_scan. Each detector must fire on a planted sample and stay
silent on a clean one, so a detector that can never fail is caught here.
Deterministic: temp dirs only, no network.
"""
import ast
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import larp_scan as ls  # noqa: E402


def kinds(src: str, name: str = "test_x.py") -> list[str]:
    tree = ast.parse(src)
    out = ls.check_tests(tree, name) + ls.check_claims(src, tree, name)
    return [f["kind"] for f in out]


class AssertionFreeTest(unittest.TestCase):
    def test_fires_on_test_with_no_assertion(self):
        src = "def test_runs():\n    x = 1 + 1\n"
        self.assertIn("assertion-free-test", kinds(src))

    def test_silent_when_asserting(self):
        src = "import unittest\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertEqual(1 + 1, 2)\n"
        self.assertNotIn("assertion-free-test", kinds(src))

    def test_plain_assert_counts_as_assertion(self):
        src = "def test_ok():\n    assert 1 + 1 == 2\n"
        self.assertNotIn("assertion-free-test", kinds(src))

    def test_helper_not_named_test_is_not_checked(self):
        src = "def helper():\n    x = 1\n"
        self.assertNotIn("assertion-free-test", kinds(src))


class SameFileHelper(unittest.TestCase):
    def test_assertion_inside_local_helper_counts(self):
        src = ("import unittest\nclass T(unittest.TestCase):\n"
               "    def _expect(self, x):\n        self.assertEqual(x, 1)\n"
               "    def test_x(self):\n        self._expect(1)\n")
        self.assertNotIn("assertion-free-test", kinds(src))

    def test_helper_without_assertion_still_fires(self):
        src = ("def _noop(x):\n    return x\n"
               "def test_x():\n    _noop(1)\n")
        self.assertIn("assertion-free-test", kinds(src))


class TrivialAssertion(unittest.TestCase):
    def test_assert_true_constant_fires(self):
        self.assertIn("trivial-assertion", kinds("def test_x():\n    assert True\n"))

    def test_assert_true_literal_method_fires(self):
        src = "import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        self.assertTrue(True)\n"
        self.assertIn("trivial-assertion", kinds(src))

    def test_self_equal_name_fires(self):
        src = "import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        y = 1\n        self.assertEqual(y, y)\n"
        self.assertIn("trivial-assertion", kinds(src))

    def test_determinism_check_on_calls_is_silent(self):
        src = "import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        self.assertEqual(f(7), f(7))\n"
        self.assertNotIn("trivial-assertion", kinds(src))

    def test_real_comparison_is_silent(self):
        src = "import unittest\nclass T(unittest.TestCase):\n    def test_x(self):\n        self.assertEqual(f(), 3)\n"
        self.assertNotIn("trivial-assertion", kinds(src))


class ClaimWithoutReceipt(unittest.TestCase):
    def test_docstring_claim_without_receipt_fires(self):
        src = 'def build():\n    """Guaranteed to work with every input."""\n'
        self.assertIn("claim-without-receipt", kinds(src, "mod.py"))

    def test_comment_claim_without_receipt_fires(self):
        src = "x = 1  # all tests pass now\n"
        self.assertIn("claim-without-receipt", kinds(src, "mod.py"))

    def test_claim_with_receipt_is_silent(self):
        src = ('def build():\n    """Guaranteed by the check below.\n\n'
               '    $ python3 -m unittest discover -s tests\n    exit: 0\n    """\n')
        self.assertNotIn("claim-without-receipt", kinds(src, "mod.py"))

    def test_plain_description_is_silent(self):
        src = 'def build():\n    """Builds the report from the inputs."""\n'
        self.assertNotIn("claim-without-receipt", kinds(src, "mod.py"))


class ScanEndToEnd(unittest.TestCase):
    def test_detector_does_not_flag_its_own_source(self):
        # Regression: the docstring once quoted claim words and flagged itself.
        self.assertEqual(ls.scan_file(Path(ls.__file__).resolve(), Path(ls.__file__).resolve().parent), [])

    def test_scan_dir_reports_planted_file_and_exits_strict(self):
        with tempfile.TemporaryDirectory() as d:
            tests = Path(d) / "tests"
            tests.mkdir()
            (tests / "test_bad.py").write_text("def test_hollow():\n    y = 2\n", encoding="utf-8")
            (tests / "test_good.py").write_text("def test_ok():\n    assert 2 == 2\n", encoding="utf-8")
            files = list(ls.iter_py([d]))
            findings = []
            for p in files:
                findings += ls.scan_file(p.resolve(), Path(d).resolve())
            self.assertEqual([f["kind"] for f in findings], ["assertion-free-test"])
            self.assertTrue(findings[0]["file"].endswith("test_bad.py"))
            self.assertEqual(ls.main(["--strict", d]), 1)

    def test_clean_dir_exits_zero_under_strict(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "test_ok.py").write_text("def test_ok():\n    assert len('ab') == 2\n", encoding="utf-8")
            self.assertEqual(ls.main(["--strict", d]), 0)

    def test_unparseable_file_is_reported_not_crashing(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "broken.py"
            bad.write_text("def (:\n", encoding="utf-8")
            out = ls.scan_file(bad.resolve(), Path(d).resolve())
            self.assertEqual([f["kind"] for f in out], ["unparseable"])


if __name__ == "__main__":
    unittest.main()
