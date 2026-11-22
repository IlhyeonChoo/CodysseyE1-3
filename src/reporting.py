"""Display call-weighted benchmark results for each matrix size."""

from itertools import groupby
from operator import itemgetter
from typing import Collection, Iterable


def print_benchmark_table(
    results: Iterable[dict], fallback_sizes: Collection[int] = (), *,
    source_label: str = "입력",
) -> None:
    """Compare layouts when each result contains a paired measurement."""
    by_size = itemgetter("n")
    ordered = sorted(results, key=by_size)
    paired = bool(ordered) and all("flat_average_ms" in item for item in ordered)
    print("\n성능 분석")
    if paired:
        print("크기\t2D 평균(ms)\t1D 평균(ms)\t배속(2D/1D)\t연산 횟수(N²)\t방식별 MAC 호출 수\t데이터")
    else:
        print("크기\t평균 시간(ms)\t연산 횟수(N²)\tMAC 호출 수\t데이터")
    for n, group in groupby(ordered, key=by_size):
        calls = 0
        total_ms = 0.0
        flat_ms = 0.0
        for result in group:
            calls += result["repeats"]
            total_ms += result["repeats"] * result["average_ms"]
            if paired:
                flat_ms += result["repeats"] * result["flat_average_ms"]
        columns = [f"{n}×{n}", f"{total_ms / calls:.6f}"]
        if paired:
            ratio = f"{total_ms / flat_ms:.2f}" if flat_ms else "—"
            columns.extend([f"{flat_ms / calls:.6f}", ratio])
        source = "대체" if n in fallback_sizes else source_label
        columns.extend([str(n * n), str(calls), source])
        print("\t".join(columns))
