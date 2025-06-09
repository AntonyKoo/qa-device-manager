import os
import socket
import requests
from dotenv import load_dotenv
from utils.qr_generator import generate_qr_images

load_dotenv()

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
IP_FILE = "last_known_ip.txt"


def get_local_ip():
    """현재 내부망에서 사용할 수 있는 로컬 IP 반환"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 인터넷 연결된 외부 IP를 흉내 내기 위한 가상 연결
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
    """QR 리스트 페이지를 포함한 Slack 알림 전송"""
    msg = f"""⚠️ 서버 IP가 변경되었습니다: `{ip}`
📎 새로운 QR 코드 보러가기 👉 http://{ip}:5000/qrs"""
    try:
        requests.post(SLACK_WEBHOOK, json={"text": msg})
        print("✅ Slack 전송 완료")
    except Exception as e:
        print("❌ Slack 전송 실패:", e)


def check_ip_and_generate(devices):
    """IP 변경 여부 확인 후 QR 생성 및 Slack 알림"""
    current_ip = get_local_ip()
    if not current_ip:
        print("❌ 내부 IP 확인 실패")
        return

    last_ip = load_last_ip()
    if current_ip != last_ip:
        print(f"🔄 IP 변경 감지: {last_ip} → {current_ip}")
        save_current_ip(current_ip)
        generate_qr_images(devices, current_ip)
        notify_slack(current_ip)
    else:
        print("✅ IP 변경 없음. QR 생성 생략.")
