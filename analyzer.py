import json
import re
import anthropic
from config import ANTHROPIC_API_KEY

CACHE_FILE = "last_output.json"

SYSTEM_PROMPT = """당신은 Reddit 트렌드에서 1인 창업 아이디어를 발굴하는 분석가입니다.

입력으로 Reddit 인기 게시물 목록이 주어지면, 그중에서 한국 시장에서 1인 개발자가 만들 수 있는 서비스 아이디어를 1~2개 뽑아주세요.

응답 형식:
- 반드시 아래 JSON 형식으로만 응답하세요.
- JSON 외에 어떤 텍스트도 출력하지 마세요. 인사말, 설명, 코드블록(```) 없이 { 로 시작하세요.
- 모든 값은 한국어 순수 텍스트로 작성하세요. 별표, 샵, 백틱 등 특수 기호를 값에 넣지 마세요.
- 모든 필드를 반드시 채우세요. 빈 문자열("")은 허용하지 않습니다.

{
  "ideas": [
    {
      "title": "서비스 이름을 짧게",
      "summary": "이 서비스가 뭔지 한 문장으로",
      "source": "어떤 서브레딧에서 발견했는지",
      "source_link": "해당 게시물의 permalink URL",
      "insight": "왜 이게 사업 기회인지 쉬운 말로 설명",
      "korea_fit": "상 또는 중 또는 하",
      "competitors": "한국에 비슷한 서비스가 있으면 이름, 없으면 없음",
      "solo_possible": "가능 또는 불가능",
      "mvp": "MVP로 만들 핵심 기능 3줄 이내",
      "revenue": "어떻게 돈을 벌 수 있는지"
    }
  ]
}

korea_fit은 반드시 상, 중, 하 중 하나.
solo_possible은 반드시 가능 또는 불가능 중 하나.
source_link는 입력 데이터의 URL을 그대로 사용."""


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

    if not sections:
        return "수집된 데이터가 없습니다."

    return "\n\n".join(sections)


def analyze(data: dict) -> dict:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    reddit_items = sorted(data.get("reddit", []), key=lambda x: x.get("score", 0), reverse=True)[:30]
    filtered_data = {"reddit": reddit_items}

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_message(filtered_data)}],
    )

    raw_text = message.content[0].text
    try:
        result = _extract_json(raw_text)
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"[ERROR] JSON 파싱 실패: {e}")
        print(f"[DEBUG] Claude 원문 응답:\n{raw_text[:2000]}")
        raise

    # 마크다운 잔재 제거 (방어)
    for idea in result.get("ideas", []):
        for key, value in idea.items():
            if isinstance(value, str):
                idea[key] = value.replace("**", "").replace("*", "").replace("#", "").replace("`", "").strip()

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result
