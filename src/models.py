"""Store validated matrices and per-pattern evaluation results."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .validation import validate_matrix


@dataclass
class Pattern:
    """Own an input matrix and results populated by evaluation."""

    n: int
    array: List[List[float]]
    expected: Optional[str] = None
    scores: Dict[str, float] = field(default_factory=dict, init=False)
    prediction: Optional[str] = field(default=None, init=False)
    passed: Optional[bool] = field(default=None, init=False)
    failure_reason: Optional[str] = field(default=None, init=False)

    def __post_init__(self) -> None:
        validate_matrix(self.n, self.array)
        if self.expected is not None and self.expected not in ("Cross", "X"):
            raise ValueError("expected는 정규화된 Cross 또는 X여야 합니다.")
        self.array = [[float(value) for value in row] for row in self.array]


@dataclass
class Filter:
    """Store a matrix and its normalized or manual-mode label."""

    n: int
    array: List[List[float]]
    label: str

    def __post_init__(self) -> None:
        validate_matrix(self.n, self.array)
        if self.label not in ("A", "B", "Cross", "X"):
            raise ValueError("필터 라벨은 A, B, Cross 또는 X여야 합니다.")
        self.array = [[float(value) for value in row] for row in self.array]
