"""Exercise the interactive generated-pattern analysis and benchmarks."""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from src import bonus


class GeneratedPatternModeTests(unittest.TestCase):
    def run_mode(self, *answers):
        output = io.StringIO()
        with patch("builtins.input", side_effect=answers), redirect_stdout(output):
            bonus.main()
        return output.getvalue()

    def test_generated_three_by_three_patterns_are_displayed_and_classified(self):
        output = self.run_mode("3")
        self.assertIn("0 1 0\n1 1 1\n0 1 0", output)
        self.assertIn("1 0 1\n0 1 0\n1 0 1", output)
        self.assertIn("Cross 점수: 5.0", output)
        self.assertIn("X 점수: 5.0", output)
        self.assertIn("판정: Cross", output)
        self.assertIn("판정: X", output)
        row = next(
            line.split("\t") for line in output.splitlines() if line.startswith("3×3\t")
        )
        self.assertEqual(row[4:], ["9", "40", "생성"])

    def test_invalid_sizes_retry_and_one_by_one_ties_are_visible(self):
        output = self.run_mode("bad", "0", "-1", "513", "1")
        self.assertEqual(output.count("입력 오류"), 4)
        self.assertEqual(output.count("판정: UNDECIDED"), 2)
        self.assertEqual(output.count("Cross 점수: 1.0"), 2)
        self.assertEqual(output.count("X 점수: 1.0"), 2)

    def test_fifteen_rows_are_displayed_and_larger_patterns_are_summarized(self):
        self.assertIn(" ".join(["1"] * 15), self.run_mode("15"))
        output = self.run_mode("16")
        self.assertIn("16×16", output)
        self.assertIn("원소 256개", output)
        self.assertNotRegex(output, r"(?m)^[01] (?:[01] ){14}[01]$")
        self.assertIn("판정: Cross", output)
        self.assertIn("판정: X", output)

    def test_terminal_interruptions_reach_the_main_menu_handler(self):
        for signal in (EOFError(), KeyboardInterrupt()):
            with self.subTest(signal=type(signal)), self.assertRaises(type(signal)):
                self.run_mode(signal)
