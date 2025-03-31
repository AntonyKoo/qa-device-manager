from flask import Flask, request, render_template_string
import requests
from datetime import datetime
from dotenv import load_dotenv
import os
import json

load_dotenv()
app = Flask(__name__)

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

users = sorted(os.getenv("USERS", "").split(","))
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>11+ 테스트 폰 대여 시스템</title>
    <style>
        body {
            margin: 0; padding: 0;
            background-color: #000;
            font-family: 'Helvetica Neue', sans-serif;
            color: #fff;
            display: flex; flex-direction: column;
            align-items: center;
            justify-content: start;
            min-height: 100vh;
            padding-top: 40px;
        }
        .logo {
            width: 120px; margin-bottom: 30px;
        }
        h2 {
            font-size: 22px; margin-bottom: 20px;
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
        select, button {
            font-size: 16px;
            padding: 12px;
            border-radius: 10px;
            border: none;
            margin-bottom: 20px;
            width: 240px;
        }
        select {
            background-color: #222; color: #fff;
        }
        button {
            background-color: #00ff91;
            color: #000; font-weight: bold;
        }
    </style>
</head>
<body>
    <img src="/static/11+logo.png" alt="11+ 로고" class="logo">
    <h2>테스트폰 대여/반납</h2>
    <div class="device"><strong>Device Name:</strong> {{ device }}</div>
    <form method="POST">
        <select name="user" id="user-select" onchange="updateActionButton()">
            <option selected disabled hidden>사용자</option>
            {% for u in users %}
            <option value="{{ u }}">{{ users_with_status[u] }}</option>
            {% endfor %}
        </select>
        <button type="submit" id="action-button">대여하기</button>
    </form>

    <script>
        const device = "{{ device }}";
        const renter = "{{ current_renter }}";

        function updateActionButton() {
            const selectedUser = document.getElementById("user-select").value;
            const btn = document.getElementById("action-button");

            if (selectedUser === renter) {
                btn.innerText = "반납하기";
            } else {
                btn.innerText = "대여하기";
            }
        }

        {% if alert_message %}
        alert("{{ alert_message }}");
        {% endif %}
    </script>
</body>
</html>
"""

@app.route("/rent", methods=["GET", "POST"])
def rent():
    device = request.args.get("device")
    if not device:
        return "기기명이 누락되었습니다."

    alert_message = None
    current_renter = device_status.get(device)

    if request.method == "POST":
        user = request.form.get("user", "")

        # 1. 사용자 선택 안 함
        if user == "" or user == "사용자":
            alert_message = "사용자를 선택해주세요!"

        # 2. 대여 시: 이미 다른 기기 대여 중
        elif device not in device_status and user in device_status.values():
            alert_message = "이미 다른 기기를 대여 중입니다!"

        # 3. 반납 시: 선택한 사용자가 대여자가 아님
        elif device in device_status and current_renter != user:
            alert_message = f"{device}은(는) {current_renter}님이 대여 중입니다. {user}님은 반납할 수 없습니다!"

        else:
            today = datetime.now().strftime("%Y/%m/%d")
            is_renting = device not in device_status

            if is_renting:
                device_status[device] = user
                save_state()
                message = f"✅ [{device}] 대여됨 – 사용자: {user} – {today}"
                alert_message = f"{user}님이 {device}을 대여했습니다!"
            else:
                prev_user = device_status.get(device, user)
                message = f"🔁 [{device}] 반납됨 – 사용자: {prev_user} – {today}"
                device_status.pop(device, None)
                save_state()
                alert_message = f"{prev_user}님이 {device}을 반납했습니다!"

            requests.post(SLACK_WEBHOOK, json={"text": message})

    # 사용자 표시 이름 구성: "홍길동 - i1 대여중"
    users_with_status = {}
    for u in users:
        device_rented = None
        for d, renter in device_status.items():
            if renter == u:
                device_rented = d
                break
        users_with_status[u] = f"{u} - {device_rented} 대여중" if device_rented else u

    action = "대여" if device not in device_status else "반납"

    return render_template_string(
        HTML_TEMPLATE,
        device=device,
        users=users,
        users_with_status=users_with_status,
        action=action,
        current_renter=current_renter,
        alert_message=alert_message
    )

if __name__ == "__main__":
    load_state()
    app.run(host="0.0.0.0", port=5000, debug=True)
