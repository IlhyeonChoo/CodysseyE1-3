"""Console entry point for the Mini NPU simulator."""

from src import bonus, mode1, mode2


def main() -> None:
    while True:
        print("\nMini NPU Simulator")
        print("1. 사용자 입력 (3×3)")
        print("2. JSON 데이터 분석")
        print("3. Cross/X 패턴 생성 및 성능 비교")
        print("0. 종료")
        choice = input("모드 선택: ").strip()
        if choice == "0":
            print("프로그램을 종료합니다.")
            return
        elif choice == "1":
            mode1.main()
        elif choice == "2":
            mode2.main()
        elif choice == "3":
            bonus.main()
        else:
            print("0, 1, 2, 3 중 하나를 입력하세요.")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n입력을 종료합니다.")
