"""Generate reusable Cross and X matrices without imposing console limits."""

from typing import List, Tuple


def generate_patterns(n: int) -> Tuple[List[List[float]], List[List[float]]]:
    """Return independent Cross/X arrays for a positive integer size.

    Even sizes use the single row and column at zero-based index n // 2.
    """
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise ValueError("패턴 크기 N은 양의 정수여야 합니다.")
    middle = n // 2
    cross = [
        [1.0 if row == middle or column == middle else 0.0 for column in range(n)]
        for row in range(n)
    ]
    x = [
        [1.0 if row == column or row + column == n - 1 else 0.0 for column in range(n)]
        for row in range(n)
    ]
    return cross, x
