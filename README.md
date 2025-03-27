# QA Device Manager

기기 대여 및 반납을 슬랙으로 자동 로그하는 간단한 Flask 웹앱입니다.  
각 테스트 기기에는 QR코드가 붙어 있으며, 접속 시 사용자 선택 후 대여/반납을 자동 처리합니다.

## 🔧 기능

- 기기별 QR 코드 접속
- 사용자 선택 (드롭다운)
- 기기 대여 또는 반납 자동 감지
- Slack Webhook으로 로그 전송

## 🖥 실행 방법 (로컬)

```bash
pip install -r requirements.txt
python app.py
