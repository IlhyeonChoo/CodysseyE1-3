"""Compute MAC scores, record evaluations, and time validated calls."""

import math
import time
from typing import Dict, Mapping, Sequence

from .models import Filter, Pattern
from .validation import validate_pair


def mac(pattern: Pattern, filter_: Filter) -> float:
    """Accumulate row-major products of already validated matrices."""
    total = 0.0
    try:
        for row in range(pattern.n):
            for column in range(pattern.n):
                total += pattern.array[row][column] * filter_.array[row][column]
    except OverflowError:
        raise ValueError("MAC 곱셈 또는 누적 결과가 유한한 수의 범위를 벗어났습니다.") from None
    if not math.isfinite(total):
        raise ValueError("MAC 곱셈 또는 누적 결과가 유한한 수의 범위를 벗어났습니다.")
    return total


def compare_mac_scores(scores: Mapping[str, float], epsilon: float = 1e-9) -> str:
    """Choose the larger of two finite scores, with a strict tie tolerance."""
    if not isinstance(scores, Mapping) or len(scores) != 2:
        raise ValueError("서로 다른 라벨의 점수 두 개가 필요합니다.")
    if isinstance(epsilon, bool) or not isinstance(epsilon, (int, float)):
        raise ValueError("epsilon은 양의 유한한 숫자여야 합니다.")
    try:
        if not math.isfinite(epsilon) or epsilon <= 0:
            raise ValueError("epsilon은 양의 유한한 숫자여야 합니다.")
        for score in scores.values():
            if (
                isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not math.isfinite(score)
            ):
                raise ValueError("MAC 점수는 유한한 숫자여야 합니다.")
    except OverflowError:
        raise ValueError("점수와 epsilon은 float로 표현 가능한 유한한 숫자여야 합니다.") from None
    first, second = list(scores)
    if abs(scores[first] - scores[second]) < epsilon:
        return "UNDECIDED"
    return first if scores[first] > scores[second] else second


def evaluate_pattern(pattern: Pattern, filters: Sequence[Filter], epsilon: float = 1e-9) -> None:
    """Replace prior results only after validating and calculating both scores."""
    pattern.scores = {}
    pattern.prediction = None
    pattern.passed = None
    pattern.failure_reason = None
    if len(filters) != 2 or filters[0].label == filters[1].label:
        raise ValueError("서로 다른 라벨의 필터 두 개가 필요합니다.")
    for filter_ in filters:
        validate_pair(pattern, filter_)
    scores = {filter_.label: mac(pattern, filter_) for filter_ in filters}
    prediction = compare_mac_scores(scores, epsilon)
    pattern.scores = scores
    pattern.prediction = prediction
    if pattern.expected is not None:
        pattern.passed = prediction == pattern.expected
        if prediction == "UNDECIDED":
            pattern.failure_reason = "두 필터의 점수가 허용오차 안에서 동점"
        elif not pattern.passed:
            pattern.failure_reason = (
                f"판정 {prediction}이 expected {pattern.expected}와 다릅니다."
            )


def benchmark_mac(pattern: Pattern, filter_: Filter, repeats: int = 10) -> Dict[str, object]:
    """Measure one R-call interval without changing evaluation fields."""
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 10:
        raise ValueError("반복 횟수는 10 이상의 정수여야 합니다.")
    validate_pair(pattern, filter_)
    start = time.perf_counter()
    for _ in range(repeats):
        mac(pattern, filter_)
    elapsed = time.perf_counter() - start
    return {
        "n": pattern.n,
        "filter_label": filter_.label,
        "repeats": repeats,
        "average_ms": elapsed * 1000.0 / repeats,
        "op_count": pattern.n ** 2,
    }
