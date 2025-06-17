import os
import socket
import requests
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
IP_FILE = "last_known_ip.txt"


def get_local_ip():
    """현재 내부망에서 사용할 수 있는 로컬 IP 반환"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def load_last_ip():
    """마지막으로 저장된 IP 로드"""
    return open(IP_FILE).read().strip() if os.path.exists(IP_FILE) else None


def save_current_ip(ip):
    """현재 IP를 파일로 저장"""
    with open(IP_FILE, "w") as f:
        f.write(ip)


def notify_slack(ip):
    """Slack으로 새로운 접속 링크 알림 (Markdown 스타일)"""
    msg = (
        "📡 *로컬 IP가 변경되었습니다!*\n\n"
        f"📎 [대여 시스템 접속하기](http://{ip}:5000/qrs)"
    )
    try:
        requests.post(SLACK_WEBHOOK, json={"text": msg})
        print("✅ Slack 전송 완료")
    except Exception as e:
        print("❌ Slack 전송 실패:", e)


def check_and_notify_ip():
    """IP 변경 여부 확인 후 Slack 알림만 전송"""
    current_ip = get_local_ip()
    if not current_ip:
        print("❌ 내부 IP 확인 실패")
        return

    last_ip = load_last_ip()
    if current_ip != last_ip:
        print(f"🔄 IP 변경 감지: {last_ip} → {current_ip}")
        save_current_ip(current_ip)
        notify_slack(current_ip)
    else:
        print("✅ IP 변경 없음")
