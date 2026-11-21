import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUAL = "1\n0 1 0\n1 1 1\n0 1 0\n1 0 1\n0 1 0\n1 0 1\n1 0 1\n0 1 0\n1 0 1\n"


class ConsoleTests(unittest.TestCase):
    def run_app(self, script, inputs, cwd):
        result = subprocess.run(
            [sys.executable, str(script)],
            input=inputs,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_json_from_another_working_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            output = self.run_app(ROOT / "main.py", "2\n", directory)
        for line in ("총 테스트: 6개", "통과: 3개", "실패: 3개"):
            self.assertIn(line, output)
        self.assertIn("25×25\t", output)

    def test_missing_file_returns_to_menu_then_completes_manual_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copy(ROOT / "main.py", root)
            shutil.copytree(
                ROOT / "src",
                root / "src",
                ignore=shutil.ignore_patterns("__pycache__"),
            )
            output = self.run_app(
                root / "main.py", "invalid\n2\n" + MANUAL, root
            )
        self.assertIn("data.json", output)
        self.assertIn("A 점수: 1.0", output)
        self.assertIn("B 점수: 5.0", output)
        self.assertIn("판정: B", output)

    def test_table_uses_call_weighted_means_and_marks_fallback(self):
        from src.reporting import print_benchmark_table

        results = [
            dict(n=3, filter_label="A", average_ms=1.0, repeats=10, op_count=9),
            dict(n=3, filter_label="B", average_ms=4.0, repeats=20, op_count=9),
        ]
        stream = io.StringIO()
        with redirect_stdout(stream):
            print_benchmark_table(results, fallback_sizes={3})
        row = next(
            line.split("\t") for line in stream.getvalue().splitlines()
            if line.startswith("3×3\t")
        )
        self.assertEqual(float(row[1]), 3.0)
        self.assertEqual(row[2:], ["9", "30", "대체"])
