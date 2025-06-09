import requests, os
from dotenv import load_dotenv
from utils.qr_generator import generate_qr_images

load_dotenv()

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK")
IP_FILE = "last_known_ip.txt"

def get_current_ip():
    try:
        return requests.get("https://api.ipify.org").text.strip()
    except:
        return None

def load_last_ip():
    return open(IP_FILE).read().strip() if os.path.exists(IP_FILE) else None

def save_current_ip(ip):
    with open(IP_FILE, "w") as f:
        f.write(ip)

def notify_slack(ip):
    msg = f"""⚠️ 서버 IP가 변경되었습니다: `{ip}`
📎 새로운 QR 코드 보러가기 👉 http://{ip}:5000/qrs"""
    requests.post(SLACK_WEBHOOK, json={"text": msg})

def check_ip_and_generate(devices):
    current_ip = get_current_ip()
    if not current_ip:
        print("❌ 외부 IP 확인 실패")
        return
    last_ip = load_last_ip()
    if current_ip != last_ip:
        save_current_ip(current_ip)
        generate_qr_images(devices, current_ip)
        notify_slack(current_ip)
