#!/usr/bin/env python3
"""
sync_card_deck.py — 一鍵從 Google Drive 拉取「卡片堆」所有 .gdoc 檔案

用法：
  python scripts/sync_card_deck.py

流程：
  1. 檢查是否已有 token → 有則直接用
  2. 沒有 → 自動開瀏覽器，完成 OAuth 認證（不用手動貼 code）
  3. 找到 Google Drive 上的「卡片堆」資料夾
  4. 下載所有 .gdoc 檔案到本地
  5. 解析並產出 game_cards.json

需要：
  - apps/backend/config/credentials.json（從 Google Cloud Console 下載）
  - pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

import json
import sys
import os
from pathlib import Path

# ─── Paths ───
BACKEND_ROOT = Path(__file__).resolve().parent.parent / "apps" / "backend"
CREDENTIALS_PATH = BACKEND_ROOT / "config" / "credentials.json"
TOKEN_PATH = BACKEND_ROOT / "data" / "google_tokens.json"
EXPORT_DIR = Path(__file__).resolve().parent.parent / "apps" / "game-rpg" / "data" / "gdrive_export"
OUTPUT_JSON = Path(__file__).resolve().parent.parent / "apps" / "game-rpg" / "data" / "game_cards.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
]

# Card deck folder name to search for
CARD_DECK_FOLDER_NAME = "卡片堆"


def get_credentials():
    """Load existing token or run OAuth flow."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    # Try loading existing token
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_info(
                json.loads(TOKEN_PATH.read_text(encoding="utf-8")), SCOPES
            )
            if creds and creds.valid:
                print("✅ 已有有效的 Google Drive 認證")
                return creds
            if creds and creds.expired and creds.refresh_token:
                print("🔄 刷新過期的 token...")
                creds.refresh(Request())
                TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
                print("✅ Token 刷新成功")
                return creds
        except Exception as e:
            print(f"⚠️ 讀取 token 失敗: {e}")

    # No valid token — run OAuth flow
    if not CREDENTIALS_PATH.exists():
        print(f"❌ 找不到 {CREDENTIALS_PATH}")
        print()
        print("請先下載 Google Cloud OAuth 憑證：")
        print("  1. 到 https://console.cloud.google.com/")
        print("  2. 建立專案 → APIs & Services → Credentials")
        print("  3. 建立 OAuth 2.0 Client ID（類型：Desktop app）")
        print("  4. 下載 JSON，放到上述路徑")
        sys.exit(1)

    print("🌐 正在開啟瀏覽器進行 Google 帳號認證...")
    print("   （瀏覽器會自動開啟，完成授權後視窗會自動關閉）")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
    # port=0 → 自動找可用 port，開本地伺服器接收回調
    creds = flow.run_local_server(port=0)

    # Save token for next time
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    print()
    print(f"✅ 認證成功！Token 已存到 {TOKEN_PATH}")
    return creds


def find_card_deck_folder(service):
    """Find the '卡片堆' folder on Google Drive."""
    results = service.files().list(
        q=f"name='{CARD_DECK_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id, name, parents)",
        pageSize=10,
    ).execute()

    folders = results.get("files", [])
    if not folders:
        print(f"❌ 找不到名為「{CARD_DECK_FOLDER_NAME}」的資料夾")
        print("   請確認 Google Drive 上有這個資料夾")
        sys.exit(1)

    if len(folders) > 1:
        print(f"⚠️ 找到 {len(folders)} 個「{CARD_DECK_FOLDER_NAME}」資料夾，使用第一個：")
        for i, f in enumerate(folders):
            print(f"   [{i+1}] {f['name']} (id={f['id']})")

    folder = folders[0]
    print(f"📁 找到卡片堆：{folder['name']} (id={folder['id']})")
    return folder["id"]


def list_gdoc_files(service, folder_id):
    """List all .gdoc files in the folder (recursively)."""
    all_files = []
    page_token = None

    while True:
        query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document' and trashed=false"
        params = {
            "q": query,
            "fields": "nextPageToken,files(id,name,parents,mimeType,modifiedTime)",
            "pageSize": 1000,
        }
        if page_token:
            params["pageToken"] = page_token

        results = service.files().list(**params).execute()
        all_files.extend(results.get("files", []))
        page_token = results.get("nextPageToken")
        if not page_token:
            break

    # Also check subfolders
    subfolders = service.files().list(
        q=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
        fields="files(id,name)",
        pageSize=100,
    ).execute()

    for subfolder in subfolders.get("files", []):
        sub_files = list_gdoc_files(service, subfolder["id"])
        all_files.extend(sub_files)

    return all_files


def download_gdoc(service, file_id, file_name, dest_dir):
    """Export a Google Doc as plain text and save locally."""
    try:
        content = service.files().export(
            fileId=file_id, mimeType="text/plain"
        ).execute()

        if isinstance(content, bytes):
            text = content.decode("utf-8", errors="replace")
        else:
            text = str(content)

        # Save with .txt extension (original was .gdoc)
        safe_name = Path(file_name).stem + ".txt"
        dest_path = dest_dir / safe_name
        dest_path.write_text(text, encoding="utf-8")
        return dest_path
    except Exception as e:
        print(f"   ⚠️ 下載失敗 {file_name}: {e}")
        return None


def main():
    from googleapiclient.discovery import build

    print("=" * 60)
    print("  Google Drive 卡片堆同步工具")
    print("=" * 60)
    print()

    # Step 1: Authenticate
    creds = get_credentials()
    service = build("drive", "v3", credentials=creds)

    # Step 2: Find card deck folder
    folder_id = find_card_deck_folder(service)

    # Step 3: List all .gdoc files
    print()
    print("🔍 掃描卡片堆中的 Google 文件...")
    files = list_gdoc_files(service, folder_id)
    print(f"   找到 {len(files)} 個 .gdoc 檔案")

    if not files:
        print("   沒有檔案可下載")
        sys.exit(0)

    # Step 4: Download
    print()
    print(f"📥 下載到 {EXPORT_DIR} ...")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    failed = 0
    for i, f in enumerate(files, 1):
        print(f"   [{i}/{len(files)}] {f['name']}", end=" ")
        result = download_gdoc(service, f["id"], f["name"], EXPORT_DIR)
        if result:
            downloaded += 1
            print("✅")
        else:
            failed += 1

    print()
    print(f"📊 下載完成：{downloaded} 成功，{failed} 失敗")
    print(f"📂 檔案位置：{EXPORT_DIR}")

    # Step 5: Optionally run card parser if it exists
    parser = Path(__file__).resolve().parent / "parse_card_deck.py"
    if parser.exists():
        print()
        print("🔄 執行卡片解析器...")
        os.system(f"python {parser}")


if __name__ == "__main__":
    main()
