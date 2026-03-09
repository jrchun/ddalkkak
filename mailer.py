import resend
from datetime import date
from config import RESEND_API_KEY, SENDER_EMAIL, RECEIVER_EMAIL

# 표시 순서: (JSON 키, 한국어 레이블, 색상, 폰트크기, 굵기)
FIELD_MAP = [
    ("title",         "아이디어명",          "#1a1a1a", "18px", "700"),
    ("summary",       "한 줄 설명",          "#444444", "14px", "400"),
    ("source",        "발견 출처",           "#888888", "13px", "400"),
    ("insight",       "핵심 인사이트",       "#222222", "14px", "400"),
    ("korea_fit",     "한국 시장 적합성",    "#222222", "14px", "400"),
    ("competitors",   "유사 서비스",         "#222222", "14px", "400"),
    ("solo_possible", "1인 개발 가능 여부",  "#222222", "14px", "400"),
    ("mvp",           "MVP 핵심 기능",       "#222222", "14px", "400"),
    ("revenue",       "예상 수익 모델",      "#222222", "14px", "400"),
]

LABEL_STYLE = (
    "font-size:11px;font-weight:600;color:#aaaaaa;"
    "text-transform:uppercase;letter-spacing:0.6px;margin:0 0 3px;"
)
DIVIDER_STYLE = "border:none;border-top:1px solid #f0f0f0;margin:12px 0;"


def _render_card(idx: int, idea: dict) -> str:
    rows = []
    for i, (key, label, color, size, weight) in enumerate(FIELD_MAP):
        value = str(idea.get(key, "")).strip()
        if not value:
            continue
        divider = f'<hr style="{DIVIDER_STYLE}">' if i > 0 else ""
        rows.append(f"""
        <div style="padding:10px 20px;">
          {divider}
          <p style="{LABEL_STYLE}">{label}</p>
          <p style="margin:0;font-size:{size};font-weight:{weight};color:{color};line-height:1.6;">{value}</p>
        </div>""")

    return f"""
    <div style="margin-bottom:24px;border:1px solid #e8e8e8;border-radius:12px;overflow:hidden;">
      <div style="background:#1a1a1a;padding:10px 20px;">
        <span style="font-size:11px;font-weight:600;color:#888888;letter-spacing:1px;">IDEA {idx}</span>
      </div>
      {"".join(rows)}
    </div>"""


def _build_html(data: dict) -> str:
    ideas = data.get("ideas", [])
    idea_sections_html = "".join(
        _render_card(idx, idea) for idx, idea in enumerate(ideas, start=1)
    )
    today = date.today().strftime("%Y년 %m월 %d일")

    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f0f0f0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f0f0;padding:32px 16px;">
    <tr>
      <td align="center">
        <div style="max-width:600px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">

          <!-- 헤더 -->
          <div style="background:#1a1a1a;padding:28px 32px;">
            <div style="font-size:26px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">딸깍 🔔</div>
            <div style="font-size:13px;color:#aaaaaa;margin-top:6px;">{today} · 오늘의 아이디어</div>
          </div>

          <!-- 본문 -->
          <div style="padding:28px 24px;">
            <p style="font-size:15px;color:#444;line-height:1.7;margin:0 0 24px;">
              오늘 트렌드에서 발굴한 서비스 아이디어예요.<br>
              1인 창업 관점으로 분석했습니다.
            </p>
            {idea_sections_html}
          </div>

          <!-- 푸터 -->
          <div style="background:#fafafa;border-top:1px solid #eeeeee;padding:20px 24px;text-align:center;">
            <p style="font-size:13px;color:#aaaaaa;margin:0;">오늘도 딸깍과 함께 좋은 하루 ☀️</p>
          </div>

        </div>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send(data: dict) -> None:
    resend.api_key = RESEND_API_KEY

    today_str = date.today().strftime("%Y-%m-%d")
    subject = f"[딸깍] {today_str} 오늘의 아이디어"

    try:
        params: resend.Emails.SendParams = {
            "from": SENDER_EMAIL,
            "to": [RECEIVER_EMAIL],
            "subject": subject,
            "html": _build_html(data),
        }
        response = resend.Emails.send(params)
        print(f"[SUCCESS] 메일 발송 완료 → {RECEIVER_EMAIL} (id: {response['id']})")
    except Exception as e:
        print(f"[FAIL] 메일 발송 실패: {e}")
