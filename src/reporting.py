"""Display call-weighted benchmark results for both input modes."""

from itertools import groupby
from operator import itemgetter
from typing import Collection, Iterable


def print_benchmark_table(
    results: Iterable[dict], fallback_sizes: Collection[int] = ()
) -> None:
    """Group measurements by matrix size and print the average per MAC call."""
    print("\n성능 분석")
    print("크기\t평균 시간(ms)\t연산 횟수(N²)\tMAC 호출 수\t데이터")
    by_size = itemgetter("n")
    for n, group in groupby(sorted(results, key=by_size), key=by_size):
        calls = 0
        total_ms = 0.0
        for result in group:
            calls += result["repeats"]
            total_ms += result["repeats"] * result["average_ms"]
        source = "대체" if n in fallback_sizes else "입력"
        print(f"{n}×{n}\t{total_ms / calls:.6f}\t{n * n}\t{calls}\t{source}")
