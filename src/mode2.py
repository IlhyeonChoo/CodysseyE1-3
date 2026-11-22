"""Load, evaluate, and benchmark the labeled patterns in a JSON file."""

import json
import re
from pathlib import Path
from typing import Dict, Tuple

from .calculator import benchmark_mac_layouts, evaluate_pattern
from .models import Filter, Pattern
from .patterns import generate_patterns
from .reporting import print_benchmark_table
from .validation import normalize_expected, normalize_filter_label, parse_pattern_key


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "data.json"
BENCHMARK_SIZES = (3, 5, 13, 25)
FilterGroups = Dict[int, Dict[str, Filter]]


def _read_document(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as source:
        document = json.load(source)
    if not isinstance(document, dict):
        raise ValueError("JSON 최상위 값은 객체여야 합니다.")
    if not isinstance(document.get("patterns"), dict):
        raise ValueError("patterns가 없거나 객체가 아닙니다.")
    return document


def _read_filter_pair(n: int, group: object) -> Dict[str, Filter]:
    if not isinstance(group, dict):
        raise ValueError("필터 그룹은 객체여야 합니다.")
    pair = {}
    for key, array in group.items():
        label = normalize_filter_label(key)
        pair[label] = Filter(n, array, label)
    if set(pair) != {"Cross", "X"}:
        raise ValueError("cross와 x 필터가 모두 필요합니다.")
    return pair


def _load_filters(groups: object) -> Tuple[FilterGroups, Dict[int, str]]:
    filters: FilterGroups = {}
    errors: Dict[int, str] = {}
    if not isinstance(groups, dict):
        print("필터 오류: filters가 없거나 객체가 아닙니다.")
        return filters, errors
    for key, group in groups.items():
        match = re.fullmatch(r"size_([1-9][0-9]*)", key)
        if not match:
            print(f"필터 키 오류: {key!r} (size_N 형식이 필요합니다.)")
            continue
        try:
            n = int(match.group(1))
        except ValueError:
            print(f"필터 크기 오류: {key!r}")
            continue
        try:
            filters[n] = _read_filter_pair(n, group)
        except ValueError as error:
            errors[n] = f"{key} 필터 오류: {error}"
            print(errors[n])
        else:
            print(f"{key} 필터 로드 완료 (Cross, X)")
    return filters, errors


def _read_pattern(case_id: str, case: object) -> Pattern:
    n = parse_pattern_key(case_id)
    if not isinstance(case, dict):
        raise ValueError("케이스는 객체여야 합니다.")
    for key in ("input", "expected"):
        if key not in case:
            raise ValueError(f"{key} 키가 없습니다.")
    return Pattern(n, case["input"], normalize_expected(case["expected"]))


def _analyze_cases(
    cases: dict, filters: FilterGroups, filter_errors: Dict[int, str]
) -> Tuple[Dict[str, Pattern], Dict[str, str]]:
    patterns: Dict[str, Pattern] = {}
    failures: Dict[str, str] = {}
    for case_id, case in cases.items():
        print(f"\n--- {case_id} ---")
        try:
            pattern = _read_pattern(case_id, case)
            patterns[case_id] = pattern
            if pattern.n not in filters:
                missing = f"size_{pattern.n} 필터가 없습니다."
                raise ValueError(filter_errors.get(pattern.n, missing))
            evaluate_pattern(pattern, tuple(filters[pattern.n].values()))
        except ValueError as error:
            reason = str(error)
            if case_id in patterns:
                patterns[case_id].passed = False
                patterns[case_id].failure_reason = reason
            failures[case_id] = reason
            print(f"FAIL ({reason})")
            continue
        for label in ("Cross", "X"):
            print(f"{label} 점수: {pattern.scores[label]!r}")
        result = "PASS"
        if not pattern.passed:
            failures[case_id] = pattern.failure_reason
            result = f"FAIL ({pattern.failure_reason})"
        print(f"판정: {pattern.prediction} | expected: {pattern.expected} | {result}")
    return patterns, failures


def _fallback_pair(n: int) -> Tuple[Pattern, Tuple[Filter, Filter]]:
    cross, x = generate_patterns(n)
    return Pattern(n, cross), (Filter(n, cross, "Cross"), Filter(n, x, "X"))


def _benchmark(patterns: Dict[str, Pattern], filters: FilterGroups) -> None:
    results = []
    measured_sizes = set()
    for pattern in patterns.values():
        if pattern.prediction is None:
            continue
        for filter_ in filters[pattern.n].values():
            results.append(benchmark_mac_layouts(pattern, filter_))
        measured_sizes.add(pattern.n)
    fallback_sizes = set(BENCHMARK_SIZES) - measured_sizes
    for n in sorted(fallback_sizes):
        pattern, pair = _fallback_pair(n)
        for filter_ in pair:
            results.append(benchmark_mac_layouts(pattern, filter_))
    print_benchmark_table(results, fallback_sizes)


def main(path: Path = DATA_PATH) -> bool:
    """Analyze one JSON file and return whether the analysis completed."""
    try:
        document = _read_document(path)
    except (OSError, ValueError, RecursionError) as error:
        print(f"JSON 파일 오류 ({path}): {error}")
        return False

    print("\n필터 로드")
    filters, filter_errors = _load_filters(document.get("filters"))
    cases = document["patterns"]
    patterns, failures = _analyze_cases(cases, filters, filter_errors)
    _benchmark(patterns, filters)

    print("\n결과 요약")
    print(f"총 테스트: {len(cases)}개")
    print(f"통과: {len(cases) - len(failures)}개")
    print(f"실패: {len(failures)}개")
    if failures:
        print("실패 케이스:")
        for case_id, reason in failures.items():
            print(f"- {case_id}: {reason}")
    return True
