import anthropic
from config import ANTHROPIC_API_KEY

SYSTEM_PROMPT = """너는 시장성 있는 서비스를 발굴하는 1인 창업 전문 기획자야.

역할:
- 입력된 영어 원문(뉴스, 레딧 게시물)을 읽고 한국 시장 관점에서 분석해
- 이미 한국에 잘 만들어진 유사 서비스가 있으면 솔직하게 언급해
- 1인 개발자가 Claude Code로 만들 수 있는 현실적인 규모인지 평가해

출력 규칙:
- 반드시 한국어로 작성
- 마크다운 절대 사용 금지. **, *, #, ` 등 마크다운 기호를 일절 쓰지 말고 순수 텍스트로만 응답
- 아이디어는 최대 2개. 퀄리티가 확실한 것만 선정하고, 1개가 낫다면 1개만 뽑아
- 각 아이디어는 아래 형식을 정확히 따를 것

---
아이디어명:
한 줄 설명:
발견 출처: (어느 서브레딧 또는 뉴스에서 나왔는지)
핵심 인사이트:
한국 시장 적합성:
유사 서비스: (있으면 명시, 없으면 "없음")
1인 개발 가능 여부: (가능 / 어려움 / 불가)
MVP 핵심 기능: (3줄 이내)
예상 수익 모델:
---"""


def _build_user_message(data: dict) -> str:
    sections = []

    reddit_items = data.get("reddit", [])
    if reddit_items:
        lines = ["[레딧 게시물]"]
        for item in reddit_items:
            lines.append(
                f"- [{item['subreddit']}] {item['title']} "
                f"(score: {item['score']}, comments: {item['num_comments']})\n"
                f"  {item['selftext']}"
            )
        sections.append("\n".join(lines))

    news_items = data.get("news", [])
    if news_items:
        lines = ["[뉴스]"]
        for item in news_items:
            lines.append(
                f"- {item['title']} ({item['published']})\n"
                f"  {item['summary']}"
            )
        sections.append("\n".join(lines))

    if not sections:
        return "수집된 데이터가 없습니다."

    return "\n\n".join(sections)


def analyze(data: dict) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    user_message = _build_user_message(data)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text
