import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

CACHE_FILE = "last_output.json"
REPORT_FILE = "test_report.json"

REQUIRED_FIELDS = [
    "title", "summary", "source", "insight",
    "korea_fit", "competitors", "solo_possible", "mvp", "revenue",
]


def run_tests() -> dict:
    checks = []
    data = None

    # ── 캐시 파일 존재 ──────────────────────────────────────────────────
    if not Path(CACHE_FILE).exists():
        checks.append({
            "name": "캐시 파일 존재",
            "passed": False,
            "detail": f"{CACHE_FILE} 파일이 없습니다",
        })
        return _save_report(checks, data)

    # ── 유효한 JSON ─────────────────────────────────────────────────────
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        checks.append({"name": "유효한 JSON", "passed": True, "detail": ""})
    except json.JSONDecodeError as e:
        checks.append({"name": "유효한 JSON", "passed": False, "detail": str(e)})
        return _save_report(checks, data)

    # ── 아이디어 1개 이상 ───────────────────────────────────────────────
    ideas = data.get("ideas", [])
    checks.append({
        "name": "아이디어 1개 이상",
        "passed": len(ideas) >= 1,
        "detail": "" if len(ideas) >= 1 else "ideas 배열이 비어 있습니다",
    })
    if not ideas:
        return _save_report(checks, data)

    # ── 필수 필드 존재 ──────────────────────────────────────────────────
    missing = []
    for i, idea in enumerate(ideas):
        for field in REQUIRED_FIELDS:
            if field not in idea:
                missing.append(f"아이디어{i + 1}.{field}")
    checks.append({
        "name": "필수 필드 존재",
        "passed": not missing,
        "detail": ", ".join(missing),
    })

    # ── 마크다운 잔재 없음 ──────────────────────────────────────────────
    md_violations = []
    for i, idea in enumerate(ideas):
        for field, value in idea.items():
            v = str(value)
            if "**" in v or re.search(r"\*[^*\s]", v):
                md_violations.append(f"아이디어{i + 1}.{field}")
    checks.append({
        "name": "마크다운 잔재 없음",
        "passed": not md_violations,
        "detail": ", ".join(md_violations),
    })

    # ── 빈 필드 없음 ────────────────────────────────────────────────────
    empty_fields = []
    for i, idea in enumerate(ideas):
        for field in REQUIRED_FIELDS:
            if field in idea and not str(idea[field]).strip():
                empty_fields.append(f"아이디어{i + 1}.{field}")
    checks.append({
        "name": "빈 필드 없음",
        "passed": not empty_fields,
        "detail": ", ".join(empty_fields),
    })

    # ── korea_fit 유효값 ────────────────────────────────────────────────
    invalid_kf = [
        f"아이디어{i + 1}: '{idea.get('korea_fit')}'"
        for i, idea in enumerate(ideas)
        if idea.get("korea_fit") not in ("상", "중", "하")
    ]
    checks.append({
        "name": "korea_fit 유효값",
        "passed": not invalid_kf,
        "detail": ", ".join(invalid_kf),
    })

    # ── solo_possible 유효값 ────────────────────────────────────────────
    invalid_sp = [
        f"아이디어{i + 1}: '{idea.get('solo_possible')}'"
        for i, idea in enumerate(ideas)
        if idea.get("solo_possible") not in ("가능", "불가능")
    ]
    checks.append({
        "name": "solo_possible 유효값",
        "passed": not invalid_sp,
        "detail": ", ".join(invalid_sp),
    })

    # ── HTML 렌더링 검증 ────────────────────────────────────────────────
    try:
        from mailer import _build_html
        html = _build_html(data)

        has_md = "**" in html
        checks.append({
            "name": "HTML 마크다운 없음",
            "passed": not has_md,
            "detail": "** 감지됨" if has_md else "",
        })

        card_count = html.count("IDEA ")
        checks.append({
            "name": "아이디어 카드 독립 렌더링",
            "passed": card_count == len(ideas),
            "detail": "" if card_count == len(ideas)
                      else f"카드 {card_count}개 / 아이디어 {len(ideas)}개",
        })
    except Exception as e:
        checks.append({"name": "HTML 마크다운 없음", "passed": False, "detail": str(e)})
        checks.append({"name": "아이디어 카드 독립 렌더링", "passed": False, "detail": "HTML 렌더링 실패로 스킵"})

    return _save_report(checks, data)


def _save_report(checks: list[dict], data: Optional[dict]) -> dict:
    ideas = data.get("ideas", []) if data else []
    passed = all(c["passed"] for c in checks)

    report = {
        "timestamp": datetime.now().isoformat(),
        "passed": passed,
        "checks": checks,
        "ideas_count": len(ideas),
        "sample_title": ideas[0].get("title", "") if ideas else "",
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    total = len(checks)
    ok = sum(1 for c in checks if c["passed"])
    status = "SUCCESS" if passed else "FAIL"
    print(f"[{status}] {ok}/{total} 통과")
    for c in checks:
        if not c["passed"]:
            print(f"  ✗ {c['name']}: {c['detail']}")

    return report


if __name__ == "__main__":
    run_tests()
