import requests
import sys
import logging
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000/api/v1/drive"

def get_url():
    try:
        response = requests.get(f"{BASE_URL}/auth/url", timeout=10)
        if response.status_code == 200:
            data = response.json()
            url = data.get("url", "")
            print(f"授權 URL：\n{url}")
            print("\n請用瀏覽器打開連結，授權後把回傳的 code 貼到：")
            print("  python scripts/exchange_drive_code.py <code>")
        elif response.status_code == 503:
            print(f"❌ 設定檔問題：{response.json().get('detail', '')}")
            print("請確認 config/credentials.json 存在且包含真實的 client_id / client_secret")
            sys.exit(1)
        else:
            print(f"Error: {response.status_code} - {response.text}", file=sys.stderr)
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接後端。請先啟動：run_angela.py", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    get_url()
