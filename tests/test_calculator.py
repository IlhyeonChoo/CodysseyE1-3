"""Verify numeric validation, MAC evaluation, and isolated benchmarking."""

import json
import math
from pathlib import Path
import unittest

from src.calculator import (
    benchmark_mac,
    compare_mac_scores,
    evaluate_pattern,
    mac,
)
from src.models import Filter, Pattern
from src.validation import (
    normalize_expected,
    normalize_filter_label,
    parse_pattern_key,
    validate_matrix,
    validate_pair,
)


class ValidationTests(unittest.TestCase):
    def test_matrix_accepts_finite_signed_numbers(self):
        self.assertIsNone(validate_matrix(2, [[1, -2.5], [0, 1e300]]))

    def test_matrix_rejects_bad_shapes_and_numbers(self):
        invalid = [
            (True, [[1]]), (0, []), (2, [[1]]), (1, [1]),
            (1, [[True]]), (1, [["1"]]), (1, [[math.nan]]),
            (1, [[math.inf]]), (1, [[-math.inf]]), (1, [[10 ** 1000]]),
            (1, None), (1, {"row": [1]}),
        ]
        for n, array in invalid:
            with self.subTest(n=n, array_type=type(array).__name__):
                with self.assertRaises(ValueError):
                    validate_matrix(n, array)

    def test_keys_and_labels_follow_documented_contract(self):
        self.assertEqual(parse_pattern_key("size_13_2"), 13)
        self.assertEqual(parse_pattern_key("size_5_0"), 5)
        self.assertEqual(parse_pattern_key("size_005_000"), 5)
        self.assertEqual(normalize_expected("+"), "Cross")
        self.assertEqual(normalize_expected("x"), "X")
        self.assertEqual(normalize_filter_label("cross"), "Cross")
        self.assertEqual(normalize_filter_label("x"), "X")
        for value in [None, [], "+", "size_0_1", "size_5_1_extra"]:
            with self.subTest(key=value):
                with self.assertRaises(ValueError):
                    parse_pattern_key(value)
        for value in [None, [], "Cross", "X", " x "]:
            with self.subTest(label=value):
                with self.assertRaises(ValueError):
                    normalize_expected(value)
        for value in [None, [], "+", "Cross", "X"]:
            with self.subTest(filter_label=value):
                with self.assertRaises(ValueError):
                    normalize_filter_label(value)

    def test_pair_validation_checks_both_matrices(self):
        pattern = Pattern(1, [[1]])
        filter_ = Filter(2, [[1, 0], [0, 1]], "A")
        with self.assertRaises(ValueError):
            validate_pair(pattern, filter_)
        filter_ = Filter(1, [[1]], "A")
        filter_.array[0][0] = math.nan
        with self.assertRaises(ValueError):
            validate_pair(pattern, filter_)


class CalculationTests(unittest.TestCase):
    def test_manual_example_matches_mission(self):
        cross = Filter(3, [[0, 1, 0], [1, 1, 1], [0, 1, 0]], "A")
        x = Filter(3, [[1, 0, 1], [0, 1, 0], [1, 0, 1]], "B")
        pattern = Pattern(3, x.array)
        self.assertIsNone(evaluate_pattern(pattern, [cross, x]))
        self.assertEqual(pattern.scores, {"A": 1.0, "B": 5.0})
        self.assertEqual(pattern.prediction, "B")
        self.assertIsNone(pattern.passed)
        self.assertIsNone(pattern.failure_reason)

    def test_supplied_data_matches_actual_scores_and_totals(self):
        path = Path(__file__).resolve().parents[1] / "data" / "data.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        failures = []
        for case_id, case in data["patterns"].items():
            n = parse_pattern_key(case_id)
            pattern = Pattern(n, case["input"], normalize_expected(case["expected"]))
            filters = [
                Filter(n, array, normalize_filter_label(label))
                for label, array in data["filters"][f"size_{n}"].items()
            ]
            evaluate_pattern(pattern, filters)
            if not pattern.passed:
                failures.append(case_id)
                self.assertEqual(pattern.prediction, "UNDECIDED")
        self.assertEqual(failures, ["size_5_1", "size_13_2", "size_25_1"])
        self.assertEqual(len(data["patterns"]), 6)

    def test_comparison_uses_strict_epsilon_boundary(self):
        self.assertEqual(compare_mac_scores({"A": 0.0, "B": 0.5e-9}), "UNDECIDED")
        self.assertEqual(compare_mac_scores({"A": 0.0, "B": 1e-9}), "B")
        self.assertEqual(compare_mac_scores({"A": -2.0, "B": -3.0}), "A")
        for scores, epsilon in [({"A": 1.0}, 1e-9), ({"A": math.inf, "B": 1.0}, 1e-9),
                                ({"A": 1.0, "B": 2.0}, 0.0)]:
            with self.subTest(scores=scores, epsilon=epsilon):
                with self.assertRaises(ValueError):
                    compare_mac_scores(scores, epsilon)

    def test_evaluation_replaces_stale_results(self):
        pattern = Pattern(1, [[1]], "X")
        filters = [Filter(1, [[1]], "Cross"), Filter(1, [[2]], "X")]
        evaluate_pattern(pattern, filters)
        self.assertTrue(pattern.passed)
        filters[0].array[0][0] = 3.0
        evaluate_pattern(pattern, filters)
        self.assertEqual(pattern.scores, {"Cross": 3.0, "X": 2.0})
        self.assertFalse(pattern.passed)
        self.assertIn("expected", pattern.failure_reason)
        filters[0].array[0][0] = math.nan
        with self.assertRaises(ValueError):
            evaluate_pattern(pattern, filters)
        self.assertEqual(pattern.scores, {})
        self.assertIsNone(pattern.prediction)
        self.assertIsNone(pattern.passed)
        self.assertIsNone(pattern.failure_reason)

    def test_duplicate_filter_labels_are_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_pattern(Pattern(1, [[1]]), [Filter(1, [[1]], "A"), Filter(1, [[2]], "A")])

    def test_pattern_results_are_not_shared(self):
        first, second = Pattern(1, [[1]]), Pattern(1, [[1]])
        first.scores["A"] = 1.0
        self.assertEqual(second.scores, {})

    def test_mac_rejects_product_and_accumulation_overflow(self):
        with self.assertRaises(ValueError):
            mac(Pattern(1, [[1e308]]), Filter(1, [[2]], "A"))
        with self.assertRaises(ValueError):
            mac(Pattern(2, [[1e308, 1e308], [0, 0]]),
                Filter(2, [[1, 1], [0, 0]], "A"))

    def test_benchmark_preserves_evaluation_results(self):
        pattern = Pattern(1, [[2]], "X")
        filters = [Filter(1, [[1]], "Cross"), Filter(1, [[2]], "X")]
        evaluate_pattern(pattern, filters)
        previous = (
            dict(pattern.scores), pattern.prediction, pattern.passed, pattern.failure_reason
        )
        result = benchmark_mac(pattern, filters[0], repeats=10)
        self.assertEqual(set(result), {"n", "filter_label", "repeats", "average_ms", "op_count"})
        self.assertEqual(
            (result["n"], result["filter_label"], result["repeats"], result["op_count"]),
            (1, "Cross", 10, 1),
        )
        self.assertGreaterEqual(result["average_ms"], 0.0)
        self.assertEqual(
            (pattern.scores, pattern.prediction, pattern.passed, pattern.failure_reason),
            previous,
        )
        for repeats in [9, True, 10.5]:
            with self.subTest(repeats=repeats):
                with self.assertRaises(ValueError):
                    benchmark_mac(pattern, filters[0], repeats=repeats)


if __name__ == "__main__":
    unittest.main()
