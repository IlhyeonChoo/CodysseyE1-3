"""Check fair timing and numerical equivalence of flat MAC storage."""

import copy
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from src.calculator import (
    _mac_flat,
    benchmark_mac_layouts,
    evaluate_pattern,
    mac,
)
from src.models import Filter, Pattern
from src.validation import normalize_expected, normalize_filter_label, validate_pair


class FlatMacTests(unittest.TestCase):
    def test_flat_kernel_preserves_signed_values_and_row_major_rounding(self):
        self.assertEqual(
            _mac_flat([1.5, -2.0, 0.25, 0.5], [2.0, 0.5, -4.0, 0.25]),
            1.125,
        )
        self.assertEqual(_mac_flat([1.0] * 9, [0.1] * 9), 0.8999999999999999)

    def test_supplied_float_data_has_identical_scores_and_preserves_results(self):
        path = Path(__file__).resolve().parents[1] / "data" / "data.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        for case_id, case in document["patterns"].items():
            n = int(case_id.split("_")[1])
            pattern = Pattern(n, case["input"], normalize_expected(case["expected"]))
            filters = [
                Filter(n, array, normalize_filter_label(label))
                for label, array in document["filters"][f"size_{n}"].items()
            ]
            evaluate_pattern(pattern, filters)
            previous = copy.deepcopy(pattern)
            original_scores = pattern.scores
            for filter_ in filters:
                with self.subTest(case=case_id, label=filter_.label):
                    original_filter = copy.deepcopy(filter_)
                    result = benchmark_mac_layouts(pattern, filter_, repeats=10)
                    self.assertEqual(
                        set(result),
                        {"n", "filter_label", "repeats", "average_ms",
                         "op_count", "flat_average_ms"},
                    )
                    self.assertEqual(result["n"], n)
                    self.assertEqual(result["filter_label"], filter_.label)
                    self.assertEqual(result["repeats"], 10)
                    self.assertEqual(result["op_count"], n * n)
                    for key in ("average_ms", "flat_average_ms"):
                        self.assertTrue(math.isfinite(result[key]))
                        self.assertGreaterEqual(result[key], 0.0)
                    self.assertEqual(pattern, previous)
                    self.assertIs(pattern.scores, original_scores)
                    self.assertEqual(filter_, original_filter)

    def test_both_intervals_use_same_repeats_with_score_checks_outside(self):
        pattern = Pattern(2, [[1.5, -2.0], [0.25, 0.5]])
        filter_ = Filter(2, [[2.0, 0.5], [-4.0, 0.25]], "A")
        timed = False
        ticks = iter((10.0, 10.02, 20.0, 20.04))
        calls = {"matrix": [], "flat": [], "validation": []}

        def clock():
            nonlocal timed
            timed = not timed
            return next(ticks)

        def tracked_mac(pattern_arg, filter_arg):
            calls["matrix"].append(timed)
            return mac(pattern_arg, filter_arg)

        def tracked_flat(values, weights):
            calls["flat"].append(timed)
            return _mac_flat(values, weights)

        def tracked_validation(pattern_arg, filter_arg):
            calls["validation"].append(timed)
            return validate_pair(pattern_arg, filter_arg)

        with patch("src.calculator.time.perf_counter", side_effect=clock), \
                patch("src.calculator.mac", side_effect=tracked_mac), \
                patch("src.calculator._mac_flat", side_effect=tracked_flat), \
                patch("src.calculator.validate_pair", side_effect=tracked_validation):
            result = benchmark_mac_layouts(pattern, filter_, repeats=10)
        self.assertEqual(calls["matrix"], [False] + [True] * 10)
        self.assertEqual(calls["flat"], [False] + [True] * 10)
        self.assertEqual(calls["validation"], [False])
        self.assertAlmostEqual(result["average_ms"], 2.0)
        self.assertAlmostEqual(result["flat_average_ms"], 4.0)

    def test_score_mismatch_is_reported_explicitly(self):
        pattern = Pattern(1, [[1]])
        filter_ = Filter(1, [[1]], "A")
        with patch("src.calculator._mac_flat", return_value=2.0):
            with self.assertRaisesRegex(ValueError, "점수"):
                benchmark_mac_layouts(pattern, filter_)

    def test_overflow_is_rejected_by_both_layouts(self):
        cases = [
            ([[1e308]], [[2.0]]),
            ([[1e308, 1e308], [0.0, 0.0]], [[1.0, 1.0], [0.0, 0.0]]),
            ([[1e308, -1e308], [0.0, 0.0]], [[2.0, 2.0], [0.0, 0.0]]),
        ]
        for values, weights in cases:
            with self.subTest(size=len(values), weights=weights):
                pattern = Pattern(len(values), values)
                filter_ = Filter(len(weights), weights, "A")
                previous = copy.deepcopy(pattern)
                with self.assertRaises(ValueError):
                    benchmark_mac_layouts(pattern, filter_)
                self.assertEqual(pattern, previous)
                with self.assertRaises(ValueError):
                    _mac_flat(
                        [value for row in values for value in row],
                        [value for row in weights for value in row],
                    )

    def test_invalid_repeats_shapes_and_mutated_values_are_rejected(self):
        pattern = Pattern(1, [[1]])
        filter_ = Filter(1, [[2]], "A")
        for repeats in (True, 9, 10.5):
            with self.subTest(repeats=repeats):
                with self.assertRaises(ValueError):
                    benchmark_mac_layouts(pattern, filter_, repeats=repeats)
        with self.assertRaises(ValueError):
            benchmark_mac_layouts(pattern, Filter(2, [[1, 0], [0, 1]], "A"))
        pattern.array[0][0] = math.nan
        with self.assertRaises(ValueError):
            benchmark_mac_layouts(pattern, filter_)


if __name__ == "__main__":
    unittest.main()
