import json
import sys
import time

from collector import collect
from analyzer import analyze
from test_runner import run_tests
from mailer import send


def _save_collected(data: dict) -> None:
    with open("last_collected.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_last_output() -> dict:
    with open("last_output.json", encoding="utf-8") as f:
        return json.load(f)


def main():
    start = time.time()

    # ── 1. 수집 ─────────────────────────────────────────────────────────
    print("[1/4] 레딧 상위 포스트 수집 중...")
    try:
        collected = collect()
    except Exception as e:
        print(f"[ERROR] 수집 실패: {e}")
        sys.exit(1)

    reddit_count = len(collected.get("reddit", []))
    print(f"      레딧 {reddit_count}건 수집 완료")

    if reddit_count == 0:
        print("[ERROR] 수집된 데이터가 없어 파이프라인을 종료합니다.")
        sys.exit(1)

    _save_collected(collected)

    # ── 2. 분석 ─────────────────────────────────────────────────────────
    print("[2/4] Claude 분석 중...")
    try:
        result = analyze(collected)
    except Exception as e:
        print(f"[ERROR] 분석 실패: {e}")
        sys.exit(1)

    titles = [idea.get("title", "") for idea in result.get("ideas", [])]
    if titles:
        print(f"      생성된 아이디어: {' / '.join(titles)}")

    # ── 3. 검증 ─────────────────────────────────────────────────────────
    print("[3/4] 출력 검증 중...")
    report = run_tests()

    if not report["passed"]:
        print("      검증 실패 — 개선 에이전트 실행")
        from improve_agent import run_improve_loop
        success = run_improve_loop()

        if not success:
            print("[ERROR] 3회 개선 후에도 검증 실패. 메일 발송을 중단합니다.")
            sys.exit(1)

        # 개선 후 갱신된 결과 로드
        result = _load_last_output()
        titles = [idea.get("title", "") for idea in result.get("ideas", [])]
        print(f"      개선 완료: {' / '.join(titles)}")

    # ── 4. 발송 ─────────────────────────────────────────────────────────
    print("[4/4] 메일 발송 중...")
    try:
        send(result)
    except Exception as e:
        print(f"[ERROR] 메일 발송 실패: {e}")
        sys.exit(1)

    elapsed = time.time() - start
    print(f"\n완료! 전체 실행 시간: {elapsed:.1f}초")


if __name__ == "__main__":
    main()
