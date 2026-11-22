"""Console entry point for the Mini NPU simulator."""

from src import bonus, mode1, mode2


def main() -> None:
    print("Mini NPU Simulator")
    while True:
        print("\n1. 사용자 입력 (3×3)\n2. JSON 데이터 분석\n3. Cross/X 패턴 생성 및 성능 비교")
        choice = input("모드 선택: ").strip()
        if choice == "1":
            mode1.main()
            return
        elif choice == "2":
            if mode2.main():
                return
        elif choice == "3":
            bonus.main()
            return
        else:
            print("1, 2, 3 중 하나를 입력하세요.")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n입력을 종료합니다.")
