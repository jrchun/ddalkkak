import json
import re
import anthropic
from config import ANTHROPIC_API_KEY

CACHE_FILE = "last_output.json"

SYSTEM_PROMPT = """너는 시장성 있는 서비스를 발굴하는 1인 창업 전문 기획자야.

역할:
- 입력된 영어 원문(뉴스, 레딧 게시물)을 읽고 한국 시장 관점에서 분석해
- 이미 한국에 잘 만들어진 유사 서비스가 있으면 솔직하게 언급해
- 1인 개발자가 Claude Code로 만들 수 있는 현실적인 규모인지 평가해
- 개발 지식이 상대적으로 적은 창업가도 이해할 수 있도록 전문 용어 없이 쉽게 풀어서 설명해. 기술 용어가 꼭 필요하면 괄호 안에 한 줄로 부연 설명을 달아줘.

출력 규칙:
- 반드시 한국어로 작성
- 마크다운 절대 사용 금지. **, *, #, ` 등 마크다운 기호를 일절 쓰지 말고 순수 텍스트로만 응답
- 아이디어는 최대 2개. 퀄리티가 확실한 것만 선정하고, 1개가 낫다면 1개만 뽑아
- 응답은 반드시 아래 JSON 형식만 출력. 코드 블록(```)이나 설명 텍스트 없이 순수 JSON 객체만.

{
  "ideas": [
    {
      "title": "아이디어명",
      "summary": "한 줄 설명",
      "source": "어느 서브레딧 또는 뉴스 매체에서 나왔는지",
      "source_link": "해당 게시물 또는 기사의 원본 URL",
      "insight": "핵심 인사이트 (쉬운 말로)",
      "korea_fit": "상 또는 중 또는 하",
      "competitors": "유사 서비스 (없으면 없음)",
      "solo_possible": "가능 또는 불가능",
      "mvp": "MVP 핵심 기능 (3줄 이내, 쉬운 말로)",
      "revenue": "예상 수익 모델"
    }
  ]
}

주의:
- korea_fit은 반드시 "상", "중", "하" 중 하나만 사용
- solo_possible은 반드시 "가능" 또는 "불가능" 중 하나만 사용
- source_link는 입력 데이터에 포함된 실제 URL을 그대로 사용할 것
- 모든 필드를 빈 값 없이 채울 것"""


def _extract_json(text: str) -> dict:
    """응답 텍스트에서 JSON을 추출하고 파싱."""
    # 마크다운 코드 블록 제거
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = text.replace("```", "").strip()

    # 중괄호로 감싸진 JSON 영역 추출
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group()

    return json.loads(text)


def _build_user_message(data: dict) -> str:
    sections = []

    reddit_items = data.get("reddit", [])
    if reddit_items:
        lines = ["[레딧 게시물]"]
        for item in reddit_items:
            lines.append(
                f"- [{item['subreddit']}] {item['title']} "
                f"(score: {item['score']}, comments: {item['num_comments']})\n"
                f"  URL: {item['permalink']}\n"
                f"  {item['selftext']}"
            )
        sections.append("\n".join(lines))

    news_items = data.get("news", [])
    if news_items:
        lines = ["[뉴스]"]
        for item in news_items:
            lines.append(
                f"- {item['title']} ({item['published']})\n"
                f"  URL: {item['link']}\n"
                f"  {item['summary']}"
            )
        sections.append("\n".join(lines))

    if not sections:
        return "수집된 데이터가 없습니다."

    return "\n\n".join(sections)


def analyze(data: dict) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_message(data)}],
    )

    result = _extract_json(message.content[0].text)

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result
