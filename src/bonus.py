"""Generate Cross and X patterns, classify them, and compare MAC layouts."""

from .calculator import benchmark_mac_layouts, evaluate_pattern
from .models import Filter, Pattern
from .patterns import generate_patterns
from .reporting import print_benchmark_table


MAX_SIZE = 512
DISPLAY_LIMIT = 15


def _read_size() -> int:
    while True:
        value = input(f"패턴 크기 N (1~{MAX_SIZE}): ")
        try:
            n = int(value)
        except ValueError:
            n = 0
        if 1 <= n <= MAX_SIZE:
            return n
        print(f"입력 오류: 1부터 {MAX_SIZE}까지의 정수를 입력하세요.")


def main() -> None:
    """Analyze both generated patterns against the same pair of filters."""
    n = _read_size()
    cross, x = generate_patterns(n)
    filters = (Filter(n, cross, "Cross"), Filter(n, x, "X"))
    results = []
    for source in filters:
        pattern = Pattern(n, source.array)
        print(f"\n{source.label} 패턴 ({n}×{n})")
        if n <= DISPLAY_LIMIT:
            for row in pattern.array:
                print(" ".join(str(int(value)) for value in row))
        else:
            print(f"원소 {n * n}개 · 배열 출력 생략")
        evaluate_pattern(pattern, filters)
        for label, score in pattern.scores.items():
            print(f"{label} 점수: {score}")
        print(f"판정: {pattern.prediction}")
        for filter_ in filters:
            results.append(benchmark_mac_layouts(pattern, filter_))
    print_benchmark_table(results, source_label="생성")
