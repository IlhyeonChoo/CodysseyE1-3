"""Check generated geometry and its reuse in manual input mode."""

import contextlib
import io
import unittest
from unittest.mock import patch

from src import mode1
from src.patterns import generate_patterns


CROSS_ROWS = ["0 1 0", "1 1 1", "0 1 0"]
X_ROWS = ["1 0 1", "0 1 0", "1 0 1"]


class GeneratedPatternTests(unittest.TestCase):
    """Verify the Cross/X construction independently of MAC scoring."""

    def test_three_by_three_matches_the_mission_shapes(self):
        cross, x = generate_patterns(3)
        self.assertEqual(cross, [[0.0, 1.0, 0.0], [1.0, 1.0, 1.0], [0.0, 1.0, 0.0]])
        self.assertEqual(x, [[1.0, 0.0, 1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 1.0]])
        self.assertTrue(all(type(value) is float for row in cross + x for value in row))

    def test_even_size_uses_one_zero_based_middle_row_and_column(self):
        cross, x = generate_patterns(4)
        self.assertEqual(cross, [
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [1.0, 1.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 0.0],
        ])
        self.assertEqual(x, [
            [1.0, 0.0, 0.0, 1.0],
            [0.0, 1.0, 1.0, 0.0],
            [0.0, 1.0, 1.0, 0.0],
            [1.0, 0.0, 0.0, 1.0],
        ])

    def test_single_cell_generates_both_patterns(self):
        self.assertEqual(generate_patterns(1), ([[1.0]], [[1.0]]))

    def test_rows_patterns_and_calls_do_not_share_mutable_arrays(self):
        cross, x = generate_patterns(3)
        cross[0][0] = 9.0
        cross[1][1] = 8.0
        x[0][1] = 7.0
        self.assertEqual(cross[2][0], 0.0)
        self.assertEqual(x[1][1], 1.0)
        self.assertEqual(x[2][1], 0.0)
        fresh_cross, fresh_x = generate_patterns(3)
        self.assertEqual(fresh_cross[0][0], 0.0)
        self.assertEqual(fresh_x[0][1], 0.0)

    def test_invalid_sizes_are_rejected(self):
        for invalid in (0, -1, True, False, 3.0, "3", None):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    generate_patterns(invalid)

    def test_shared_helper_does_not_apply_the_console_size_limit(self):
        cross, x = generate_patterns(257)
        self.assertEqual(len(cross), 257)
        self.assertEqual(len(x[-1]), 257)
        self.assertEqual(cross[128][0], 1.0)
        self.assertEqual(x[-1][-1], 1.0)


class GeneratedManualInputTests(unittest.TestCase):
    """Exercise generation commands without replacing the real calculator."""

    def run_mode(self, rows):
        output = io.StringIO()
        with patch("builtins.input", side_effect=rows):
            with contextlib.redirect_stdout(output):
                try:
                    mode1.main()
                except StopIteration:
                    self.fail("Manual mode requested rows after a complete generation command.")
        return output.getvalue()

    def test_first_pattern_row_accepts_case_insensitive_generation_commands(self):
        cases = (
            ("  cRoSs  ", "A 점수: 5.0", "B 점수: 1.0", "판정: A"),
            (" x ", "A 점수: 1.0", "B 점수: 5.0", "판정: B"),
        )
        for command, a_score, b_score, prediction in cases:
            with self.subTest(command=command):
                output = self.run_mode(CROSS_ROWS + X_ROWS + [command])
                self.assertIn(a_score, output)
                self.assertIn(b_score, output)
                self.assertIn(prediction, output)
                self.assertIn("Cross", output)
                self.assertIn("X", output)

    def test_numeric_pattern_input_keeps_its_existing_behavior(self):
        output = self.run_mode(CROSS_ROWS + X_ROWS + X_ROWS)
        self.assertIn("A 점수: 1.0", output)
        self.assertIn("B 점수: 5.0", output)
        self.assertIn("판정: B", output)

    def test_manual_performance_includes_the_flat_layout_for_each_filter(self):
        results = []
        with patch.object(mode1, "print_benchmark_table", results.extend):
            self.run_mode(CROSS_ROWS + X_ROWS + ["X"])
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIn("flat_average_ms", result)
            self.assertGreaterEqual(result["flat_average_ms"], 0.0)

    def test_later_row_command_retries_only_the_pattern_block(self):
        output = self.run_mode(
            CROSS_ROWS + X_ROWS + ["1 0 1", "Cross", "X"]
        )
        self.assertIn("입력 형식 오류", output)
        self.assertIn("A 점수: 1.0", output)
        self.assertIn("B 점수: 5.0", output)
        self.assertIn("판정: B", output)

    def test_filters_require_numeric_rows_before_pattern_generation(self):
        output = self.run_mode(["Cross"] + CROSS_ROWS + X_ROWS + ["X"])
        self.assertIn("입력 형식 오류", output)
        self.assertIn("A 점수: 1.0", output)
        self.assertIn("B 점수: 5.0", output)
        self.assertIn("판정: B", output)


if __name__ == "__main__":
    unittest.main()
