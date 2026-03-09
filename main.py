import sys
import time

from collector import collect
from analyzer import analyze
from mailer import send


def extract_idea_titles(analysis: str) -> list[str]:
    titles = []
    for block in analysis.split("---"):
        for line in block.splitlines():
            if line.strip().startswith("아이디어명:"):
                title = line.partition(":")[2].strip()
                if title:
                    titles.append(title)
                break
    return titles


def main():
    start = time.time()

    # 1. 수집 시작
    print("[1/3] 뉴스 및 레딧 수집 중...")
    try:
        data = collect()
    except Exception as e:
        print(f"[ERROR] 수집 실패: {e}")
        sys.exit(1)

    # 2. 수집 건수 로그
    reddit_count = len(data.get("reddit", []))
    news_count = len(data.get("news", []))
    print(f"      레딧 {reddit_count}건, 뉴스 {news_count}건 수집 완료")

    if reddit_count + news_count == 0:
        print("[ERROR] 수집된 데이터가 없어 파이프라인을 종료합니다.")
        sys.exit(1)

    # 3. 분석
    print("[2/3] Claude 분석 중...")
    try:
        analysis = analyze(data)
    except Exception as e:
        print(f"[ERROR] 분석 실패: {e}")
        sys.exit(1)

    titles = extract_idea_titles(analysis)
    if titles:
        print(f"      생성된 아이디어: {' / '.join(titles)}")
    else:
        print("      (아이디어 제목을 파싱하지 못했습니다)")

    # 4. 메일 발송
    print("[3/3] 메일 발송 중...")
    try:
        send(analysis)
    except Exception as e:
        print(f"[ERROR] 메일 발송 실패: {e}")
        sys.exit(1)

    elapsed = time.time() - start
    print(f"\n완료! 전체 실행 시간: {elapsed:.1f}초")


if __name__ == "__main__":
    main()
