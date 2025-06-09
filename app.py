from flask import Flask, request, render_template_string
import requests
from datetime import datetime
from dotenv import load_dotenv
from utils.ip_monitor import check_ip_and_generate
import os
import json
from flask import render_template
from utils.qr_generator import generate_qr_images, get_local_ip

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

users = sorted([u.strip() for u in os.getenv("USERS", "").split(",")])
devices = sorted([d.strip() for d in os.getenv("DEVICES", "").split(",")])
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
            background-color: #000;
            font-family: 'Helvetica Neue', sans-serif;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding-top: 40px;
            min-height: 100vh;
        }
        .logo { width: 120px; margin-bottom: 30px; }
        h2 { font-size: 22px; margin-bottom: 20px; }
        .device { color: #00ff91; font-size: 16px; margin: 60px 0 20px 0; }
        form { display: flex; flex-direction: column; align-items: center; }
        select, button {
            font-size: 16px;
            padding: 12px;
            border-radius: 10px;
            border: none;
            margin-bottom: 20px;
            width: 240px;
        }
        select { background-color: #222; color: #fff; }
        button { background-color: #00ff91; color: #000; font-weight: bold; }
    </style>
</head>
<body>
    <img src="/static/11+logo.png" alt="11+ 로고" class="logo">
    <h2>테스트폰 대여/반납</h2>
    <div class="device"><strong>Device Name:</strong> {{ device }}</div>

    <!-- 사용자 선택 (GET) -->
    <form method="GET">
        <input type="hidden" name="device" value="{{ device }}">
        <select name="user" onchange="this.form.submit()">
            <option disabled {% if not selected_user %}selected{% endif %}>사용자</option>
            {% for u in users %}
            <option value="{{ u }}" {% if u == selected_user %}selected{% endif %}>{{ users_with_status[u] }}</option>
            {% endfor %}
        </select>
    </form>

    <!-- 대여/반납 버튼 (POST) -->
    {% if selected_user %}
    <form method="POST">
        <input type="hidden" name="user" value="{{ selected_user }}">
        <input type="hidden" name="device" value="{{ device }}">
        <button type="submit">{{ action }}하기</button>
    </form>
    {% endif %}

    {% if alert_message %}
    <script>alert("{{ alert_message }}");</script>
    {% endif %}
</body>
</html>
"""

@app.route("/rent", methods=["GET", "POST"])
def rent():
    device = request.values.get("device")
    if not device:
        return "기기명이 누락되었습니다."

    alert_message = None
    current_renter = device_status.get(device)
    selected_user = request.values.get("user", "")

    if request.method == "POST":
        print("🔥 POST 요청 들어옴!")
        user = request.form.get("user", "")
        print(f"📥 POST로 들어온 user={user}, device={device}")

        if user == "":
            alert_message = "사용자를 선택해주세요!"
        else:
            current_holder = device_status.get(device)
            user_devices = [d for d, renter in device_status.items() if renter == user]
            is_renting = device not in device_status

            # 반납 시도인데 본인이 아닌 경우
            if not is_renting and current_holder != user:
                alert_message = f"{device}은(는) {current_holder}님이 대여 중입니다. {user}님은 반납할 수 없습니다!"

            # 대여 시도
            elif is_renting:
                # 일반 사용자: 이미 다른 기기 대여 중이면 차단
                if user != "이동현" and user in device_status.values():
                    alert_message = "이미 다른 기기를 대여 중입니다!"

                # 이동현: 총 2대 초과하면 차단
                elif user == "이동현":
                    if len(user_devices) >= 2:
                        alert_message = "이동현님은 a2 외 1대만 추가 대여할 수 있습니다!"

            # 대여 또는 반납 실행
            if not alert_message:
                today = datetime.now().strftime("%Y/%m/%d")
                if is_renting:
                    device_status[device] = user
                    message = f"✅ [{device}] 대여됨 – 사용자: {user} – {today}"
                    alert_message = f"{user}님이 {device}을 대여했습니다!"
                else:
                    device_status.pop(device, None)
                    message = f"🔁 [{device}] 반납됨 – 사용자: {user} – {today}"
                    alert_message = f"{user}님이 {device}을 반납했습니다!"

                save_state()

                try:
                    requests.post(SLACK_WEBHOOK, json={"text": message})
                except Exception as e:
                    print("Slack 전송 오류:", e)

    # 사용자 상태 표시: "이름 - i1 대여중"
    users_with_status = {}
    for u in users:
        rented_devices = [d for d, renter in device_status.items() if renter == u]
        if rented_devices:
            device_str = ", ".join(rented_devices)
            users_with_status[u] = f"{u} - {device_str} 대여중"
        else:
            users_with_status[u] = u

    action = "반납" if selected_user and selected_user == current_renter else "대여"

    return render_template_string(
        HTML_TEMPLATE,
        device=device,
        users=users,
        selected_user=selected_user,
        users_with_status=users_with_status,
        current_renter=current_renter,
        action=action,
        alert_message=alert_message
    )

@app.route("/qrs")
def show_qrs():
    return render_template("qrs.html", devices=devices)


if __name__ == "__main__":
    load_state()
    check_ip_and_generate(devices)
    app.run(host="0.0.0.0", port=5000, debug=True)
