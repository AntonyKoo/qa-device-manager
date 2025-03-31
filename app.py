from flask import Flask, request, render_template_string
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = Flask(__name__)

# 상태 저장용 JSON 파일 경로
STATE_FILE = "device_status.json"
device_status = {}

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(device_status, f)

def load_state():
    global device_status
    try:
        with open(STATE_FILE, "r") as f:
            device_status = json.load(f)
    except FileNotFoundError:
        device_status = {}

# 사용자 목록과 슬랙 Webhook 불러오기
users = sorted(os.getenv("USERS", "").split(","))
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

# HTML 템플릿 (alert_message 변수 추가됨)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>11+ 테스트 폰 대여 시스템</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #000;
            font-family: 'Helvetica Neue', sans-serif;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: start;
            min-height: 100vh;
            padding-top: 40px;
        }
        .logo {
            width: 120px;
            margin-bottom: 30px;
        }
        h2 {
            font-size: 22px;
            margin-bottom: 20px;
        }
        .device {
            font-size: 16px;
            margin-top: 60px;
            margin-bottom: 20px;
            color: #00ff91;
        }
        form {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        select {
            font-size: 16px;
            padding: 12px;
            border-radius: 10px;
            border: none;
            margin-bottom: 20px;
            width: 240px;
            background-color: #222;
            color: #fff;
        }
        button {
            font-size: 16px;
            padding: 12px;
            border-radius: 10px;
            border: none;
            width: 240px;
            background-color: #00ff91;
            color: #000;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <img src="/static/11+logo.png" alt="11+ 로고" class="logo">
    <h2>테스트폰 대여/반납</h2>
    <div class="device"><strong>Device Name:</strong> {{ device }}</div>
    <form method="POST">
        <select name="user">
            <option selected disabled hidden>사용자</option>
            {% for u in users %}
            <option value="{{ u }}">{{ u }}</option>
            {% endfor %}
        </select>
        <button type="submit">{{ action }}하기</button>
    </form>

    {% if alert_message %}
    <script>alert("{{ alert_message }}");</script>
    {% endif %}
</body>
</html>
"""

@app.route("/rent", methods=["GET", "POST"])
def rent():
    device = request.args.get("device")
    if not device:
        return "기기명이 누락되었습니다."

    alert_message = None

    if request.method == "POST":
        user = request.form.get("user", "")

        if user == "" or user == "사용자":
            alert_message = "사용자를 선택해주세요!"

        elif device not in device_status and user in device_status.values():
            alert_message = "이미 대여 중인 사용자입니다!"

        else:
            today = datetime.now().strftime("%Y/%m/%d")
            is_renting = device not in device_status

            if is_renting:
                device_status[device] = user
                save_state()
                message = f"✅ [{device}] 대여됨 – 사용자: {user} – {today}"
            else:
                prev_user = device_status.get(device, user)
                message = f"🔁 [{device}] 반납됨 – 사용자: {prev_user} – {today}"
                device_status.pop(device, None)
                save_state()

            requests.post(SLACK_WEBHOOK, json={"text": message})
            return f"<h3>처리 완료</h3><p>{message}</p><a href='/rent?device={device}'>뒤로</a>"

    action = "대여" if device not in device_status else "반납"
    return render_template_string(HTML_TEMPLATE, device=device, users=users, action=action, alert_message=alert_message)

if __name__ == "__main__":
    load_state()
    app.run(host="0.0.0.0", port=5000, debug=True)
