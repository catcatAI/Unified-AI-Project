import requests
import sys
import logging
logger = logging.getLogger(__name__)

BASE_URL="http://127.0.0.1:8000/api/v1/drive"

def exchange_code(code):
    try:
        response = requests.post(f"{BASE_URL}/auth/callback", json={"code": code}, timeout=15)
        if response.status_code == 200:
            print("✅ Google Drive 認證成功！")
            print(response.json())
        elif response.status_code == 503:
            print(f"❌ 設定檔問題：{response.json().get('detail', '')}")
            sys.exit(1)
        else:
            print(f"❌ 認證失敗 ({response.status_code})：{response.text}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接後端。請先啟動：run_angela.py", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        exchange_code(sys.argv[1])
    else:
        print("用法：python scripts/exchange_drive_code.py <authorization_code>")
        print("先執行 scripts/get_drive_auth_url.py 取得授權 URL")
