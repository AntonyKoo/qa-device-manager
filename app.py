from flask import Flask, request, render_template_string, redirect
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

app = Flask(__name__)

# 기기 상태 저장 (대여중인 사용자 저장)
device_status = {}

# 사용자 목록
users = os.getenv("USERS", "").split(",")

# 슬랙 Webhook URL
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

# HTML 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>기기 대여 시스템</title></head>
<body style="font-family: sans-serif; padding: 20px;">
    <h2>기기 대여/반납</h2>
    <p><strong>기기:</strong> {{ device }}</p>
    <form method="POST">
        <label for="user">사용자 선택:</label>
        <select name="user">
            {% for u in users %}
            <option value="{{ u }}">{{ u }}</option>
            {% endfor %}
        </select><br><br>
        <button type="submit">{{ action }}하기</button>
    </form>
</body>
</html>
"""

@app.route("/rent", methods=["GET", "POST"])
def rent():
    device = request.args.get("device")
    if not device:
        return "기기명이 누락되었습니다."

    if request.method == "POST":
        user = request.form["user"]
        today = datetime.now().strftime("%Y/%m/%d")
        is_renting = device not in device_status  # True면 대여, False면 반납

        if is_renting:
            device_status[device] = user
            message = f"✅ [{device}] 대여됨 – 사용자: {user} – {today}"
        else:
            prev_user = device_status.get(device, user)
            message = f"🔁 [{device}] 반납됨 – 사용자: {prev_user} – {today}"
            device_status.pop(device, None)

        # 슬랙 전송
        requests.post(SLACK_WEBHOOK, json={"text": message})

        return f"<h3>처리 완료</h3><p>{message}</p><a href='/rent?device={device}'>뒤로</a>"

    action = "대여" if device not in device_status else "반납"
    return render_template_string(HTML_TEMPLATE, device=device, users=users, action=action)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
