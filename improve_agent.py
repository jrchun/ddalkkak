import json
import subprocess
import sys
from datetime import datetime

from test_runner import run_tests

MAX_CYCLES = 3
REPORT_FILE = "test_report.json"
LOG_FILE = "improvement_log.txt"

# 실패 체크 이름 → 삽입할 추가 지시문
PATCH_MAP = {
    "마크다운 잔재 없음":       "마크다운 완전 금지: **, *, #, `, _ 등 모든 마크다운 기호 사용 절대 금지. 순수 텍스트만 허용.",
    "HTML 마크다운 없음":       "마크다운 완전 금지: **, *, #, `, _ 등 모든 마크다운 기호 사용 절대 금지. 순수 텍스트만 허용.",
    "유효한 JSON":              "응답은 반드시 유효한 JSON 객체만 출력. 코드 블록(```) 없이, 설명 없이, 순수 JSON만 응답.",
    "필수 필드 존재":           "title, summary, source, insight, korea_fit, competitors, solo_possible, mvp, revenue 9개 필드를 모두 포함할 것.",
    "빈 필드 없음":             "어떤 필드도 빈 문자열로 두지 말 것. 모든 필드에 실질적인 내용 필수.",
    "korea_fit 유효값":         "korea_fit은 반드시 '상', '중', '하' 셋 중 하나만. 다른 값 사용 금지.",
    "solo_possible 유효값":     "solo_possible은 반드시 '가능' 또는 '불가능' 중 하나만. 다른 값 사용 금지.",
    "아이디어 카드 독립 렌더링": "ideas 배열에 아이디어를 각각 독립된 객체로 작성할 것.",
}


def _patch_analyzer(failed_checks: list[dict]) -> None:
    """실패 항목에 맞는 지시문을 analyzer.py의 SYSTEM_PROMPT에 추가."""
    patches = []
    for check in failed_checks:
        for key, instruction in PATCH_MAP.items():
            if key in check["name"] and instruction not in patches:
                patches.append(instruction)

    if not patches:
        return

    with open("analyzer.py", encoding="utf-8") as f:
        content = f.read()

    marker = 'SYSTEM_PROMPT = """'
    start = content.find(marker) + len(marker)
    end = content.find('"""', start)

    current_prompt = content[start:end]

    # 이전 자동 패치 섹션 제거
    patch_marker = "\n\n[자동 패치]"
    if patch_marker in current_prompt:
        current_prompt = current_prompt[:current_prompt.find(patch_marker)]

    patch_section = patch_marker + "\n" + "\n".join(f"- {p}" for p in patches)
    new_content = content[:start] + current_prompt + patch_section + content[end:]

    with open("analyzer.py", "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"      패치 적용: {len(patches)}개 지시문 추가")


def _reanalyze() -> bool:
    """last_collected.json으로 analyzer를 재실행해 last_output.json 갱신."""
    script = (
        "import json; from analyzer import analyze\n"
        "data = json.load(open('last_collected.json', encoding='utf-8'))\n"
        "analyze(data)"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"      재분석 오류: {result.stderr.strip()}")
        return False
    return True


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
    last_report = {}

    for cycle in range(1, MAX_CYCLES + 1):
        print(f"[사이클 {cycle}] 테스트 실행 중...")
        last_report = run_tests()

        if last_report["passed"]:
            print(f"[사이클 {cycle}] 전체 통과 ✓")
            return True

        failed = [c for c in last_report["checks"] if not c["passed"]]
        names = ", ".join(c["name"] for c in failed)
        print(f"[사이클 {cycle}] 실패: {names}")

        if cycle == MAX_CYCLES:
            break

        print(f"[사이클 {cycle}] analyzer.py 프롬프트 수정 중...")
        _patch_analyzer(failed)

        print(f"[사이클 {cycle}] 재분석 실행 중...")
        if not _reanalyze():
            print(f"[사이클 {cycle}] 재분석 실패 — 루프 중단")
            break

    _save_improvement_log(last_report)
    return False
