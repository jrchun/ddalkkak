MIN_ITEMS = 10
TOP_N = 30


def validate(collected: dict) -> dict:
    items = collected.get("reddit", [])
    total = len(items)
    issues = []

    # 데이터 무결성 검증
    valid_items = []
    dropped = 0
    for item in items:
        title = (item.get("title") or "").strip()
        permalink = (item.get("permalink") or "").strip()
        if not title or not permalink:
            dropped += 1
            issues.append(f"[무결성 실패] title='{title}', permalink='{permalink}'")
            continue
        valid_items.append(item)

    if dropped > 0:
        print(f"[VALIDATE] 무결성 실패 {dropped}건 제거")

    # 최소 수집량 검증
    if len(valid_items) < MIN_ITEMS:
        msg = f"수집량 부족: {len(valid_items)}건 (최소 {MIN_ITEMS}건 필요)"
        issues.append(msg)
        print(f"[VALIDATE] {msg}")
        return {
            "valid": False,
            "total_collected": total,
            "filtered_count": len(valid_items),
            "dropped_count": dropped,
            "reddit": valid_items,
            "issues": issues,
        }

    # score 기준 내림차순 정렬 → 상위 N개 추출
    valid_items.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_items = valid_items[:TOP_N]

    print(f"[VALIDATE] 원본 {total}건 → 무결성 통과 {len(valid_items)}건 → 상위 {len(top_items)}개 선별")

    return {
        "valid": True,
        "total_collected": total,
        "filtered_count": len(top_items),
        "dropped_count": dropped,
        "reddit": top_items,
        "issues": issues,
    }
