import resend
from datetime import date
from config import RESEND_API_KEY, SENDER_EMAIL, RECEIVER_EMAIL


def _build_html(analysis: str) -> str:
    # "---" 구분자로 아이디어 분리
    ideas = [block.strip() for block in analysis.split("---") if block.strip()]

    idea_sections_html = ""
    for idx, idea in enumerate(ideas, start=1):
        rows_html = ""
        for line in idea.splitlines():
            if ":" not in line:
                continue
            label, _, value = line.partition(":")
            label = label.strip()
            value = value.strip()
            if not label or not value:
                continue
            rows_html += f"""
            <tr>
              <td style="padding:8px 12px;font-size:13px;color:#888;white-space:nowrap;vertical-align:top;width:130px;">
                {label}
              </td>
              <td style="padding:8px 12px;font-size:14px;color:#222;line-height:1.6;">
                {value}
              </td>
            </tr>"""

        idea_sections_html += f"""
        <div style="margin-bottom:28px;border:1px solid #e8e8e8;border-radius:10px;overflow:hidden;">
          <div style="background:#f5f5f5;padding:10px 16px;font-size:13px;font-weight:600;color:#555;">
            아이디어 {idx}
          </div>
          <table style="width:100%;border-collapse:collapse;">
            {rows_html}
          </table>
        </div>"""

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


def send(analysis: str) -> None:
    resend.api_key = RESEND_API_KEY

    today_str = date.today().strftime("%Y-%m-%d")
    subject = f"[딸깍] {today_str} 오늘의 아이디어"

    try:
        params: resend.Emails.SendParams = {
            "from": SENDER_EMAIL,
            "to": [RECEIVER_EMAIL],
            "subject": subject,
            "html": _build_html(analysis),
        }
        response = resend.Emails.send(params)
        print(f"[SUCCESS] 메일 발송 완료 → {RECEIVER_EMAIL} (id: {response['id']})")
    except Exception as e:
        print(f"[FAIL] 메일 발송 실패: {e}")
