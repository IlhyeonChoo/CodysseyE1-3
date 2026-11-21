"""Exercise manual input, block recovery, and visible analysis results."""

import contextlib
import io
import unittest
from unittest.mock import patch

from src import mode1


CROSS_ROWS = ["0 1 0", "1 1 1", "0 1 0"]
X_ROWS = ["1 0 1", "0 1 0", "1 0 1"]


class ManualModeTests(unittest.TestCase):
    """Check the console contract using the real calculation pipeline."""

    def run_mode(self, rows):
        output = io.StringIO()
        with patch("builtins.input", side_effect=rows):
            with contextlib.redirect_stdout(output):
                mode1.main()
        return output.getvalue()

    def assert_x_result(self, output):
        self.assertIn("A 점수: 1.0", output)
        self.assertIn("B 점수: 5.0", output)
        self.assertIn("판정: B", output)

    def test_reference_input_prints_scores_prediction_and_performance(self):
        output = self.run_mode(CROSS_ROWS + X_ROWS + X_ROWS)
        self.assert_x_result(output)
        self.assertIn("평균", output)
        self.assertIn("ms", output)
        self.assertNotIn("PASS", output)
        self.assertNotIn("FAIL", output)

    def test_invalid_filter_b_retries_b_and_preserves_filter_a(self):
        for invalid_row in ("1 0", "wrong 0 1"):
            with self.subTest(invalid_row=invalid_row):
                output = self.run_mode(
                    CROSS_ROWS + [invalid_row] + X_ROWS + X_ROWS
                )
                self.assertIn("입력 형식 오류", output)
                self.assert_x_result(output)

    def test_empty_row_restarts_the_current_three_row_block(self):
        output = self.run_mode(
            [CROSS_ROWS[0], ""] + CROSS_ROWS + X_ROWS + X_ROWS
        )
        self.assertIn("입력 형식 오류", output)
        self.assert_x_result(output)

    def test_invalid_pattern_preserves_both_filters(self):
        output = self.run_mode(CROSS_ROWS + X_ROWS + ["bad"] + X_ROWS)
        self.assertIn("입력 형식 오류", output)
        self.assert_x_result(output)

    def test_nonfinite_filter_values_are_rejected_before_analysis(self):
        for invalid_value in ("nan", "inf", "-inf"):
            with self.subTest(invalid_value=invalid_value):
                invalid_block = [invalid_value + " 0 0", "0 0 0", "0 0 0"]
                output = self.run_mode(
                    CROSS_ROWS + invalid_block + X_ROWS + X_ROWS
                )
                self.assertIn("입력 형식 오류", output)
                self.assert_x_result(output)

    def test_epsilon_tie_is_printed_as_manual_undecided(self):
        rows = ["0.9 0 0", "0 0 0", "0 0 0"]
        rows += ["0.1 0.1 0.1"] * 3
        rows += ["1 1 1"] * 3
        output = self.run_mode(rows)
        self.assertIn("판정: 판정 불가", output)

    def test_numeric_overflow_reports_error_and_retries_pattern(self):
        large = ["1e308 0 0", "0 0 0", "0 0 0"]
        zero = ["0 0 0"] * 3
        output = self.run_mode(large + zero + large + zero)
        self.assertIn("연산 오류", output)
        self.assertIn("A 점수: 0.0", output)
        self.assertIn("B 점수: 0.0", output)
        self.assertIn("판정: 판정 불가", output)

    def test_terminal_interruptions_propagate_to_the_entrypoint(self):
        for error in (EOFError, KeyboardInterrupt):
            with self.subTest(error=error):
                with patch("builtins.input", side_effect=error):
                    with contextlib.redirect_stdout(io.StringIO()):
                        with self.assertRaises(error):
                            mode1.main()


if __name__ == "__main__":
    unittest.main()
