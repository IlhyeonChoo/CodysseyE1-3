"""Exercise JSON mode with the supplied cases and replacement files."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src import mode2


class JsonModeTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "data.json"

    def run_mode(self, *args):
        output = io.StringIO()
        with redirect_stdout(output):
            completed = mode2.main(*args)
        return completed, output.getvalue()

    def test_supplied_file_reports_three_ties_and_three_passes(self):
        completed, output = self.run_mode()
        self.assertTrue(completed)
        self.assertIn("총 테스트: 6개", output)
        self.assertIn("통과: 3개", output)
        self.assertIn("실패: 3개", output)
        failures = output.split("실패: 3개", 1)[1]
        for case_id in ("size_5_1", "size_13_2", "size_25_1"):
            self.assertIn(case_id, failures)
        self.assertEqual(output.count("Cross 점수"), 6)
        self.assertEqual(output.count("X 점수"), 6)

    def test_only_evaluated_cases_enter_benchmarks_including_failed_predictions(self):
        middle = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
        zeros = [[0] * 3 for _ in range(3)]
        twos = [[1, 1], [1, 1]]
        doc = {
            "filters": {
                "size_3": {"cross": middle, "x": zeros},
                "size_5": {"cross": []},
                "size_2": {"cross": [[0, 0], [0, 0]], "x": twos},
            },
            "patterns": {
                "size_3_1": {"input": middle, "expected": "+"},
                "size_3_2": {"input": zeros, "expected": "x"},
                "size_3_3": {"input": middle, "expected": "x"},
                "size_3_4": {"input": middle, "expected": "other"},
                "size_3_5": {"input": middle},
                "broken_key": {},
                "size_3_6": [],
                "size_5_1": {"input": [[1] * 5 for _ in range(5)], "expected": "x"},
                "size_3_7": {"input": [[1]], "expected": "x"},
                "size_2_1": {"input": twos, "expected": "x"},
            },
        }
        self.path.write_text(json.dumps(doc), encoding="utf-8")
        completed, output = self.run_mode(self.path)
        self.assertTrue(completed)
        self.assertIn("총 테스트: 10개", output)
        self.assertIn("통과: 2개", output)
        self.assertIn("실패: 8개", output)
        self.assertEqual(output.count("Cross 점수"), 4)
        self.assertEqual(output.count("X 점수"), 4)
        self.assertRegex(output, r"(?m)^3×3\s+\S+\s+9\s+60\s+입력$")
        self.assertRegex(output, r"(?m)^2×2\s+\S+\s+4\s+20\s+입력$")
        self.assertRegex(output, r"(?m)^5×5\s+\S+\s+25\s+20\s+대체$")
        failures = output.split("실패: 8개", 1)[1]
        for case_id in list(doc["patterns"])[1:-1]:
            self.assertEqual(failures.count(case_id), 1)

    def test_bad_file_returns_to_menu_before_evaluation_or_measurement(self):
        for data in (None, b"\xff", b"{", b"[]", b'{"patterns": []}', b"{}"):
            with self.subTest(data=data):
                if data is not None:
                    self.path.write_bytes(data)
                completed, output = self.run_mode(self.path)
                self.assertFalse(completed)
                self.assertIn(str(self.path), output)
                self.assertNotIn("총 테스트", output)
                self.assertNotIn("3×3", output)

    def test_missing_filter_section_counts_each_case_once(self):
        doc = {"patterns": {"size_1_1": {"input": [[1]], "expected": "+"}}}
        self.path.write_text(json.dumps(doc), encoding="utf-8")
        completed, output = self.run_mode(self.path)
        self.assertTrue(completed)
        self.assertIn("총 테스트: 1개", output)
        self.assertIn("통과: 0개", output)
        self.assertIn("실패: 1개", output)
        self.assertNotIn("Cross 점수", output)
        self.assertNotIn("1×1", output)
        self.assertIn("필터", output.split("실패: 1개", 1)[1])
        for size in (3, 5, 13, 25):
            self.assertRegex(output, rf"(?m)^{size}×{size}\s+.*\s20\s+대체$")
