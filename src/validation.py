"""Validate matrix structure, finite values, JSON keys, and labels."""

import math
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Filter, Pattern


def validate_matrix(n: int, array: object) -> None:
    """Require an N by N list containing finite int or float values."""
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise ValueError("배열 크기 N은 양의 정수여야 합니다.")
    if not isinstance(array, list) or len(array) != n:
        raise ValueError(f"행 수가 선언된 크기 {n}과 일치해야 합니다.")
    for row_index, row in enumerate(array, start=1):
        if not isinstance(row, list) or len(row) != n:
            raise ValueError(f"{row_index}행의 열 수는 {n}이어야 합니다.")
        for column_index, value in enumerate(row, start=1):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{row_index}행 {column_index}열은 숫자여야 합니다.")
            try:
                finite = math.isfinite(float(value))
            except (OverflowError, ValueError):
                finite = False
            if not finite:
                raise ValueError(
                    f"{row_index}행 {column_index}열은 "
                    "float로 표현 가능한 유한한 숫자여야 합니다."
                )


def validate_pair(pattern: "Pattern", filter_: "Filter") -> None:
    """Validate both matrices and require matching declared sizes."""
    validate_matrix(pattern.n, pattern.array)
    validate_matrix(filter_.n, filter_.array)
    if pattern.n != filter_.n:
        raise ValueError("패턴과 필터의 크기가 일치해야 합니다.")


def parse_pattern_key(case_id: object) -> int:
    """Extract positive N from size_N_idx with a nonnegative numeric idx."""
    if not isinstance(case_id, str):
        raise ValueError("패턴 키는 size_{N}_{idx} 형식의 문자열이어야 합니다.")
    match = re.fullmatch(r"size_([0-9]+)_([0-9]+)", case_id)
    if match is None:
        raise ValueError("패턴 키는 숫자 N과 idx를 가진 size_{N}_{idx} 형식이어야 합니다.")
    try:
        n = int(match.group(1))
    except ValueError:
        raise ValueError("패턴 키의 크기 N을 정수로 변환할 수 없습니다.") from None
    if n <= 0:
        raise ValueError("패턴 키의 크기 N은 양의 정수여야 합니다.")
    return n


def normalize_expected(value: object) -> str:
    """Normalize the exact expected labels accepted by the JSON schema."""
    if value == "+":
        return "Cross"
    if value == "x":
        return "X"
    raise ValueError("expected는 '+' 또는 'x'여야 합니다.")


def normalize_filter_label(value: object) -> str:
    """Normalize the exact filter keys accepted by the JSON schema."""
    if value == "cross":
        return "Cross"
    if value == "x":
        return "X"
    raise ValueError("필터 키는 'cross' 또는 'x'여야 합니다.")
