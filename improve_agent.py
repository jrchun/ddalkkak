import json
from datetime import datetime

from validator import validate
from analyzer import analyze
from test_runner import run_tests

MAX_CYCLES = 2
LOG_FILE = "improvement_log.txt"


def _save_improvement_log(last_report: dict) -> None:
    failed = [c for c in last_report["checks"] if not c["passed"]]
    lines = [
        f"[{datetime.now().isoformat()}] 개선 루프 종료 — 최종 실패",
        f"실패 항목 ({len(failed)}개):",
        *[f"  - {c['name']}: {c['detail']}" for c in failed],
        "",
    ]
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"      실패 내역 → {LOG_FILE}")


def run_improve_loop() -> bool:
    # last_collected.json 로드
    try:
        with open("last_collected.json", encoding="utf-8") as f:
            collected = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[IMPROVE] last_collected.json 로드 실패: {e}")
        return False

    validated = validate(collected)
    if not validated["valid"]:
        print("[IMPROVE] 수집 데이터가 부족하여 재분석 불가")
        return False

    last_report = {}

    for cycle in range(1, MAX_CYCLES + 1):
        print(f"[IMPROVE 사이클 {cycle}/{MAX_CYCLES}] 재분석 실행 중...")
        try:
            analyze(validated)
        except Exception as e:
            print(f"[IMPROVE 사이클 {cycle}] 재분석 실패: {e}")
            continue

        print(f"[IMPROVE 사이클 {cycle}] 테스트 실행 중...")
        last_report = run_tests()

        if last_report["passed"]:
            print(f"[IMPROVE 사이클 {cycle}] 전체 통과")
            return True

        failed = [c for c in last_report["checks"] if not c["passed"]]
        names = ", ".join(c["name"] for c in failed)
        print(f"[IMPROVE 사이클 {cycle}] 실패: {names}")

    if last_report:
        _save_improvement_log(last_report)
    return False
