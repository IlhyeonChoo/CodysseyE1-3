# Mini NPU Simulator 아키텍처

기능과 완료 조건은 `feature.md`, 미션 원문은 `mission.md`를 기준으로 한다.
이 문서는 구현할 데이터 구조, 모듈의 책임, 호출 흐름을 정의한다.
아래 파일 구성은 설계안이며, 아직 Python 구현 파일이 생성되었다는 뜻은 아니다.

## 설계 원칙

- 모드 1과 모드 2는 동일한 `Pattern`과 `Filter`를 사용한다.
- `Pattern`은 입력 배열뿐 아니라 필터별 점수, 판정, expected 비교 결과를 소유한다.
- MAC 계산과 점수 비교는 계산 함수가 수행하고, 분석 함수가 결과를 `Pattern`에 기록한다.
- 모드별 함수는 입력·출력과 오류 복구, 실행 순서를 담당한다.
- 크기별 반복 성능 측정 결과는 `Pattern`의 판정 결과와 별도로 관리한다.
- 객체의 생성자에는 입력 데이터만 전달한다. 계산 결과는 생성 시 초기화하고 분석 후 채운다.

## 디렉터리와 책임

```text
main.py
README.md
data/
    data.json
docs/
    mission.md
    feature.md
    architecture.md
src/
    __init__.py
    models.py
    validation.py
    calculator.py
    mode1.py
    mode2.py
```

| 파일 | 책임 |
| --- | --- |
| `main.py` | 모드 선택 반복, 잘못된 메뉴 입력의 재입력, 모드 실행과 파일 오류 후 메뉴 복귀 |
| `src/models.py` | `Pattern`, `Filter`와 결과 초기화 규칙 |
| `src/validation.py` | 배열·크기·JSON 키 검증, 라벨 정규화 |
| `src/calculator.py` | MAC, epsilon 비교, Pattern 결과 기록, 반복 성능 측정 |
| `src/mode1.py` | 콘솔 입력과 재입력, 수동 분석 진행, 결과 출력 |
| `src/mode2.py` | JSON 로드, 케이스별 분석과 오류 처리, 성능 표와 최종 집계 출력 |
| `README.md` | 실행 안내, 구현 요약, 실제 결과와 복잡도 분석 |

## 데이터 구조

### Pattern

생성자 계약은 `Pattern(n, array, expected=None)` 하나로 통일한다.

| 필드 | 타입 | 초기값 또는 의미 |
| --- | --- | --- |
| `n` | `int` | 배열의 한 변 크기 |
| `array` | `list[list[float]]` | 입력 패턴. 정수 입력도 실수로 변환해 저장 가능 |
| `expected` | `str \| None` | 모드 1은 `None`, 모드 2는 정규화된 `Cross` 또는 `X` |
| `scores` | `dict[str, float]` | 생성 시 빈 딕셔너리, 분석 후 필터 라벨별 점수 |
| `prediction` | `str \| None` | 생성 시 `None`, 분석 후 선택된 필터 라벨 또는 `UNDECIDED` |
| `passed` | `bool \| None` | 생성 시 `None`. 모드 1은 비교하지 않아 `None`, 모드 2는 PASS/FAIL에 대응하는 참/거짓 |
| `failure_reason` | `str \| None` | 생성 시 `None`, 모드 2에서 실패하면 원인 요약 |

- `scores`는 객체마다 새 딕셔너리로 생성한다. 여러 Pattern이 기본 딕셔너리를 공유하지 않는다.
- 모드 1은 `Pattern(3, array)`로 생성하고, `scores`의 키는 `A`, `B`를 사용한다.
- 모드 2는 `Pattern(n, array, expected=normalized_expected)`로 생성하고,
  `scores`의 키는 `Cross`, `X`를 사용한다.
- JSON 모드에서 expected는 필수다. 생성자 기본값이 `None`이어도 누락된 expected를 정상 케이스로 허용하지 않는다.
- `prediction=None`은 아직 계산하지 않은 상태이며, `UNDECIDED`는 계산을 완료한 동점 결과다.
- 모드 1에서 `UNDECIDED`는 콘솔에 `판정 불가`로 표시한다.
- 모드 2의 케이스 ID는 `dict[str, Pattern]`의 키로 보관한다.
  예: `patterns["size_5_1"]`에서 해당 Pattern과 그 결과를 조회한다.
- 원본 항목이 잘못되어 Pattern을 생성할 수 없는 경우에는 모드 2가 케이스 ID와 실패 사유를 직접 기록한다.
- `op_count`는 N과 비교하는 필터 수로 산출할 수 있으므로 Pattern의 별도 변경 가능한 필드로 중복 저장하지 않는다.

### Filter

생성자 계약은 `Filter(n, array, label)`이다.

| 필드 | 타입 | 의미 |
| --- | --- | --- |
| `n` | `int` | 배열의 한 변 크기 |
| `array` | `list[list[float]]` | 필터의 숫자 배열 |
| `label` | `str` | 모드 1은 `A` 또는 `B`, 모드 2는 `Cross` 또는 `X` |

JSON 필터는 `dict[int, dict[str, Filter]]`로 보관한다.
예: `filters[5]["Cross"]`는 정규화된 5×5 Cross 필터다.
수동 입력 필터 A/B가 실제 Cross/X 모양인지 추측하거나 검증하지 않는다.

### 성능 측정 결과

- 패턴·필터 조합별 측정 결과는 `n`, `filter_label`, `repeats`, `average_ms`, `op_count`를 담은 딕셔너리로 표현한다.
- `op_count`는 필터 하나에 대한 N²이며, Pattern을 두 필터로 판정하는 2N²와 구분한다.
- 모드 1은 입력 패턴과 A/B 두 조합, 모드 2는 모든 유효 패턴과 Cross/X 조합의 결과를 모은다.
- 크기별 평균은 `sum(average_ms * repeats) / sum(repeats)`로 집계한다.
  크기별 요약은 `n`, `total_calls`, `average_ms`, `op_count`를 담은 딕셔너리로 표현한다.
- 모드 1은 3×3 요약 한 행, 모드 2는 네 크기의 요약 행을 출력한다.
- 결과 객체를 위한 별도 클래스는 필수로 도입하지 않는다.

## 공통 함수 계약

아래 함수 이름은 구현 시 사용할 설계안이다.

| 함수 | 입력 | 반환 및 변경 사항 |
| --- | --- | --- |
| `validate_matrix(n, array)` | 크기와 배열 | 행·열 수와 숫자 여부 검증. 성공 시 `None`, 실패 시 사유를 담은 `ValueError` |
| `validate_pair(pattern, filter)` | 패턴과 필터 | 각 배열과 두 크기를 검증. 실패 시 `ValueError` |
| `parse_pattern_key(case_id)` | `size_{N}_{idx}` 키 | N 반환. 잘못된 형식은 `ValueError` |
| `normalize_expected(value)` | JSON expected | `+`를 `Cross`, `x`를 `X`로 변환. 미지원 값은 `ValueError` |
| `normalize_filter_label(value)` | JSON 필터 키 | `cross`를 `Cross`, `x`를 `X`로 변환. 미지원 값은 `ValueError` |
| `mac(pattern, filter)` | 검증된 패턴과 필터 | 반복문으로 계산한 점수 반환. Pattern의 기존 결과는 변경하지 않음 |
| `compare_mac_scores(scores, epsilon=1e-9)` | 라벨이 서로 다른 두 필터의 점수 | 선택한 라벨 또는 `UNDECIDED` 반환 |
| `evaluate_pattern(pattern, filters, epsilon=1e-9)` | Pattern과 서로 다른 라벨의 필터 두 개 | 검증·MAC·비교를 수행하고 Pattern의 결과 필드에 기록. 반환값은 `None` |
| `benchmark_mac(pattern, filter, repeats=10)` | 검증된 패턴·필터 한 조합과 10 이상의 반복 횟수 | 조합별 평균 시간과 N²를 담은 측정 결과 반환. Pattern의 판정 결과는 변경하지 않음 |
| `mode2.main()` | `data/data.json` | 분석·집계를 완료하면 `True`, 파일 전체 오류로 메뉴 복귀가 필요하면 `False` |

### 분석 결과 기록

`evaluate_pattern()`은 다음 순서로 동작한다.

1. 기존 `scores`, `prediction`, `passed`, `failure_reason`을 초기화한다.
2. 필터가 두 개이고 라벨이 서로 다른지, 패턴과 각 필터가 올바른 크기인지 검증한다.
3. 각 필터의 `mac()` 결과를 임시 딕셔너리에 계산한다.
4. `abs(score_a - score_b) < epsilon`이면 `UNDECIDED`, 그 외에는 큰 점수의 라벨을 선택한다.
5. 계산이 모두 성공하면 `pattern.scores`와 `pattern.prediction`에 기록한다.
6. expected가 있으면 비교해 `pattern.passed`를 설정한다. 동점 또는 expected 불일치 시 사유도 기록한다.

검증 실패는 호출한 모드에서 처리한다. 모드 2는 이미 생성된 Pattern이라면
`passed=False`와 실패 사유를 기록한다. Pattern 생성 전 오류는 케이스 실패 목록에 기록한다.
벤치마크는 `mac()`만 반복 호출하므로 기존 판정과 PASS/FAIL을 덮어쓰지 않는다.

### 측정 범위

- 검증과 측정용 데이터 준비를 먼저 완료한다.
- `time.perf_counter()`로 MAC 함수 호출 구간을 반복 측정하고 평균 ms를 계산한다.
- 입력·출력·파일 읽기·정규화·검증·점수 비교는 측정에서 제외한다.
- 모드 1은 3×3, 모드 2는 3×3·5×5·13×13·25×25를 측정한다.
- 모드 1은 입력 패턴과 A/B를 모두 측정한다.
- 모드 2는 각 크기의 모든 유효 패턴과 Cross/X를 각각 측정한다.
- 최소 반복 횟수는 각 패턴·필터 조합마다 10회다.
  유효 패턴 P개와 반복 횟수 R에 대해 크기별 총 호출 수는 `P × 2 × R`이다.
- 모든 호출 시간의 합을 총 호출 수로 나누어 호출당 평균 ms를 출력한다.
  표의 연산 횟수는 호출당 N²이며, 두 필터 판정 전체나 반복 전체의 횟수와 구분한다.
- 3×3은 JSON에 없으므로 고정 측정용 배열을 별도로 준비한다.
- 특정 크기에 유효한 조합이 있으면 검증 오류 케이스를 제외하고 해당 조합을 모두 측정한다.
- 유효한 조합이 전혀 없는 크기는 별도의 유효한 고정 패턴과 두 필터를 사용하며,
  대체 데이터를 사용했다는 사실을 출력한다.
  정답 비교에서 FAIL이어도 배열과 크기 검증이 통과했다면 측정 데이터로 사용할 수 있다.

## 모드별 흐름

### main.py

1. 모드 선택 메뉴를 표시한다.
2. 잘못된 선택은 안내 후 다시 받는다.
3. 선택에 따라 `mode1.main()` 또는 `mode2.main()`을 호출한다.
4. `mode2.main()`이 파일 전체 오류로 `False`를 반환하면 반복문의 처음으로 돌아가 메뉴를 다시 표시한다.
   모드 2에서 `main.py`의 진입점을 재귀 호출하지 않는다.
5. 선택한 모드가 정상 완료되면 프로그램을 종료한다.

### mode1.py

1. 필터 A/B를 행 단위로 입력받고 검증한 뒤 Filter를 생성한다.
   오류가 있으면 현재 필터의 임시 입력 전체를 비우고 3줄을 다시 받는다.
   앞서 정상 저장한 다른 필터는 유지한다.
2. 필터 저장 완료를 안내한다.
3. 패턴을 입력받고 검증한 뒤 expected 없이 Pattern을 생성한다.
   오류가 있으면 두 필터는 유지하고 패턴의 3줄만 다시 받는다.
4. `evaluate_pattern()`을 호출한다.
5. Pattern의 점수와 판정을 출력한다. expected 비교와 PASS/FAIL은 출력하지 않는다.
6. 입력된 패턴과 A/B 각각을 최소 10회 측정하고, 호출당 평균 ms와 N²를 출력한다.

### mode2.py

1. `data/data.json`을 읽고 최상위 구조를 확인한다.
   파일이 없거나 읽기·JSON 문법 오류가 있으면 원인과 경로를 출력하고 `False`를 반환한다.
   최상위 값이 객체가 아니거나 `patterns`가 없거나 딕셔너리가 아닌 경우에도 오류 안내 후 `False`를 반환한다.
   이 경우 케이스 분석·성능 측정·집계는 진행하지 않는다.
2. 크기별 필터를 검증·정규화해 저장한다. 잘못된 필터 크기는 실패 사유를 따로 보관한다.
3. 원본 patterns 항목을 하나씩 처리한다.
   - 키에서 N을 추출하고 input과 expected를 검증한다.
   - expected를 정규화하고 Pattern을 생성한다.
   - N에 맞는 두 필터로 `evaluate_pattern()`을 호출한다.
   - Pattern에 저장된 결과를 출력하고 전체·통과·실패 수에 반영한다.
   - 케이스 오류는 ID와 사유를 남기고 다음 케이스로 진행한다.
4. 네 크기의 모든 유효 패턴·필터 조합을 측정하고 크기별 호출당 평균 표를 출력한다.
5. 전체·통과·실패 수와 실패 ID·사유 목록을 출력하고 `True`를 반환한다.

원본 케이스마다 한 번만 집계하며, Pattern 생성 실패나 필터 오류도 해당 케이스의 FAIL에 포함한다.
성능 측정은 테스트 수에 포함하지 않는다.

## 오류 처리 경계

| 오류 또는 결과 | 처리 위치와 동작 |
| --- | --- |
| 수동 입력의 숫자·행·열 오류 | 현재 필터 또는 패턴의 3×3 전체를 다시 입력. 다른 정상 입력은 유지 |
| JSON 파일 없음·읽기 실패·문법 오류 | 모드 2에서 안내하고 `False` 반환. main의 모드 선택 화면으로 복귀 |
| 최상위 값이 객체가 아니거나 `patterns` 누락·타입 오류 | 케이스 목록을 만들 수 없으므로 안내 후 모드 선택 화면으로 복귀 |
| `filters` 누락 또는 잘못된 구조 | 케이스 목록이 유효하면 각 케이스를 필터 오류 FAIL로 집계 |
| 특정 크기의 필터 오류 | 해당 크기를 사용하는 케이스만 FAIL. 다른 크기는 계속 처리 |
| 개별 키·배열·expected 오류 | 해당 케이스 FAIL과 사유 기록 후 계속 처리 |
| 정상 계산 후 동점·expected 불일치 | 예외로 처리하지 않고 Pattern의 판정·비교 결과에 기록 |

## 확정된 실행 정책

- 한 필터만 대표로 고르지 않고 두 필터를 모두 측정한다. JSON은 모든 유효 패턴을 포함한다.
- 입력 오류는 현재 필터·패턴 전체를 다시 입력받으며, 정상 입력은 유지한다.
- 파일 전체 오류는 안내 후 모드 선택으로 복귀하고, 개별 케이스 오류는 FAIL 후 계속 진행한다.
