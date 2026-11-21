"""Run the interactive three-by-three pattern analysis mode."""

from __future__ import annotations

from typing import List

from src.calculator import benchmark_mac, evaluate_pattern
from src.models import Filter, Pattern
from src.reporting import print_benchmark_table
from src.validation import validate_matrix


def _read_matrix(name: str) -> List[List[float]]:
    """Read one complete matrix, retrying only its block after invalid input."""
    while True:
        print(f"{name} (3줄 입력, 각 줄에 숫자 3개)")
        matrix: List[List[float]] = []
        try:
            for row_index in range(3):
                tokens = input(f"{row_index + 1}/3> ").split()
                if len(tokens) != 3:
                    raise ValueError("빈 줄 없이 각 줄에 숫자 3개가 필요합니다.")
                matrix.append([float(token) for token in tokens])
            validate_matrix(3, matrix)
        except (ValueError, OverflowError) as error:
            print(
                "입력 형식 오류: 각 줄에 3개의 유한한 숫자를 공백으로 구분해 "
                f"입력하세요. {name} 전체를 다시 입력합니다. ({error})"
            )
            continue
        return matrix


def main() -> None:
    """Read A/B filters and a pattern, then print scores and timing results."""
    filters = [
        Filter(3, _read_matrix("필터 A"), "A"),
        Filter(3, _read_matrix("필터 B"), "B"),
    ]
    print("필터 A/B 저장 완료")

    while True:
        pattern = Pattern(3, _read_matrix("패턴"))
        try:
            evaluate_pattern(pattern, filters)
        except ValueError as error:
            print(f"연산 오류: {error} 패턴 전체를 다시 입력하세요.")
            continue

        print(f"A 점수: {pattern.scores['A']}")
        print(f"B 점수: {pattern.scores['B']}")
        prediction = pattern.prediction
        if prediction == "UNDECIDED":
            prediction = "판정 불가"
        print(f"판정: {prediction}")
        results = [benchmark_mac(pattern, item) for item in filters]
        print_benchmark_table(results)
        return
