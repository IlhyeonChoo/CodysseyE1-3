# 전체 아키텍쳐

# 디렉토리

## docs

## data

## src

# src

## utils

공통 유틸 함수
MAC 연산, 시간 측정, 검증 등

### class Pattern

__init__(self, N, array[N][N], score[], opCount, duration, result)

__init__(self, N, array[N][N], score[], result, expect : X or +)

### class Filter

__init__(self, N, array[N][N], label : X or +)

### Calculator.py

mac(Pattern, Filter) -> score, opCount, duration

compare_mac_score(Pattern.score[]) -> result:int

check_size_N(Pattern.N, Pattern.array, Filter.N, Filter.array) -> T/F

## 모드

### mode1.py

main(): 실행
input -> Filter1 -> input -> Filter2 -> input -> Pattern -> Calculator.check_size_N()
-> Calculator.mac() -> Calculator.compare_mac_score() -> print_result()

input(): 입력 받기

print_result() : 정해진 형식 따라서 점수, 연산 횟수, 소요 시간 등 출력

### mode2.py

main(): 실행
load_data() -> Filters : Filter[] -> Patterns : Pattern[]
-> Calculator.check_size_N() -> Calculator.mac() -> Calculator.compare_mac_score()
-> 반복 -> print_result()

load_data() : data/data.json 로드

print_result() : 결과 출력
