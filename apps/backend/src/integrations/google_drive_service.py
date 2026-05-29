# =============================================================================
# ANGELA-MATRIX: L2-L3 [資源接入層] βδ [B] L4
# =============================================================================
# 職責: Google Drive OAuth2 認證 + 檔案讀寫
# 維度: 認知 (β) 維度的資訊獲取 + 精神 (δ) 維度的資源感知
# =============================================================================

import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from core.interfaces.service_registry import get_registry

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
]

CREDENTIALS_PATH = Path(__file__).parent.parent.parent / "config" / "credentials.json"
TOKEN_PATH = Path(__file__).parent.parent.parent / "data" / "google_tokens.json"
DATA_DIR = Path(__file__).parent.parent.parent / "data"


class GoogleDriveService:
    def __init__(self):
        self._creds: Optional[Credentials] = None
        self._service = None
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def _create(cls) -> "GoogleDriveService":
        """Factory: create a new GoogleDriveService instance."""
        return cls()

    def _load_token(self) -> Optional[Credentials]:
        if not TOKEN_PATH.exists():
            return None
        try:
            with open(TOKEN_PATH, "r", encoding="utf-8") as f:
                token_data = json.load(f)
            return Credentials.from_authorized_user_info(token_data, SCOPES)
        except Exception as e:
            logger.warning(f"Failed to load token: {e}", exc_info=True)
            return None

    def _save_token(self, creds: Credentials) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    def is_authenticated(self) -> bool:
        self._creds = self._load_token()
        if self._creds is None:
            return False
        if not self._creds.valid:
            try:
                self._creds.refresh()
            except Exception:
                return False
            if not self._creds.valid:
                return False
            self._save_token(self._creds)
        return True

    def get_auth_url(self) -> str:
        if not CREDENTIALS_PATH.exists():
            raise FileNotFoundError(
                f"credentials.json not found at {CREDENTIALS_PATH}. "
                "Please download from Google Cloud Console and place it there."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
        auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
        return auth_url

    def exchange_code(self, code: str) -> bool:
        """Exchange authorization code for credentials (used by API /auth/callback)."""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            flow.fetch_token(code=code)
            self._creds = flow.credentials
            self._save_token(self._creds)
            return True
        except Exception as e:
            logger.error(f"Token exchange failed: {e}", exc_info=True)
            return False

    def authenticate(self) -> bool:
        """Run interactive OAuth flow — opens browser for user to authorize."""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            self._creds = flow.run_local_server(port=0)
            self._save_token(self._creds)
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {e}", exc_info=True)
            return False

    def _get_service(self):
        if self._service is not None:
            return self._service
        if not self.is_authenticated():
            raise PermissionError("Not authenticated with Google Drive")
        self._service = build("drive", "v3", credentials=self._creds, static_dll_errors=False)
        return self._service

    def list_files(self, page_size: int = 10, query: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            service = self._get_service()
            params: Dict[str, Any] = {
                "pageSize": page_size,
                "fields": "files(id,name,mimeType,size,modifiedTime,webViewLink,parents)",
            }
            if query:
                params["q"] = query
            results = service.files().list(**params).execute()
            return results.get("files", [])
        except HttpError as e:
            logger.error(f"Drive list_files error: {e}", exc_info=True)
            raise
        except PermissionError:
            raise

    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        service = self._get_service()
        return service.files().get(
            fileId=file_id,
            fields="id,name,mimeType,size,modifiedTime,webViewLink,parents,description,owners",
        ).execute()

    def download_file(self, file_id: str, dest_path: str) -> bool:
        try:
            service = self._get_service()
            dest = Path(dest_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            request = service.files().get_media(fileId=file_id)
            with open(dest, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
            logger.info(f"Downloaded file to {dest_path}")
            return True
        except HttpError as e:
            logger.error(f"Download error: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected download error: {e}", exc_info=True)
            return False

    def export_gdoc(self, file_id: str, mime_type: str = "text/plain") -> Optional[str]:
        """Export a Google-native document (gdoc) content as text."""
        try:
            service = self._get_service()
            content = service.files().export(fileId=file_id, mimeType=mime_type).execute()
            if isinstance(content, bytes):
                return content.decode("utf-8")
            return str(content)
        except HttpError as e:
            logger.error(f"Export gdoc error for {file_id}: {e}", exc_info=True)
            return None

    def search_files(self, query: str, page_size: int = 10) -> List[Dict[str, Any]]:
        return self.list_files(page_size=page_size, query=query)

    def get_storage_info(self) -> Dict[str, Any]:
        try:
            about = self._get_service().about().get(fields="storageQuota,user").execute()
            quota = about.get("storageQuota", {})
            return {
                "used": quota.get("usage", "0"),
                "total": quota.get("limit", "0"),
                "user": about.get("user", {}).get("emailAddress", "unknown"),
            }
        except Exception as e:
            logger.warning(f"Could not get storage info: {e}", exc_info=True)
            return {"used": "0", "total": "0", "user": "unknown"}

    def upload_file(self, local_path: str, drive_folder_id: Optional[str] = None, mime_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """上傳本地檔案到 Google Drive"""
        try:
            service = self._get_service()
            path = Path(local_path)
            if not path.exists():
                logger.error(f"File not found: {local_path}", exc_info=True)
                return None
            guessed_mime = mime_type or self._guess_mime(path.suffix)
            media = MediaFileUpload(str(path), mimetype=guessed_mime, resumable=True)
            file_metadata = {"name": path.name}
            if drive_folder_id:
                file_metadata["parents"] = [drive_folder_id]
            uploaded = service.files().create(body=file_metadata, media_body=media, fields="id,name,mimeType,size,webViewLink").execute()
            logger.info(f"Uploaded {path.name} to Drive (id={uploaded.get('id')})")
            return uploaded
        except Exception as e:
            logger.error(f"Upload failed: {e}", exc_info=True)
            return None

    def create_file_from_text(self, file_name: str, content: str, mime_type: str = "text/plain", drive_folder_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """建立文字檔案並上傳到 Google Drive"""
        import tempfile
        suffix = ".txt"
        if mime_type == "text/markdown":
            suffix = ".md"
        elif mime_type == "application/json":
            suffix = ".json"
        elif mime_type == "text/html":
            suffix = ".html"
        elif mime_type == "text/csv":
            suffix = ".csv"
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp_path = f.name
        try:
            result = self.upload_file(tmp_path, drive_folder_id, mime_type)
            return result
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    @staticmethod
    def _guess_mime(suffix: str) -> str:
        mapping = {
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".json": "application/json",
            ".html": "text/html",
            ".htm": "text/html",
            ".csv": "text/csv",
            ".py": "text/x-python",
            ".js": "text/javascript",
            ".ts": "text/typescript",
            ".yaml": "text/yaml",
            ".yml": "text/yaml",
            ".xml": "text/xml",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }
        return mapping.get(suffix.lower(), "text/plain")

    def logout(self) -> None:
        if TOKEN_PATH.exists():
            TOKEN_PATH.unlink()
        self._creds = None
        self._service = None
        pass


_drive_instance: Optional[GoogleDriveService] = None


def get_drive_service() -> GoogleDriveService:
    global _drive_instance
    if _drive_instance is None:
        _drive_instance = GoogleDriveService()
        get_registry().register("google_drive_service", _drive_instance)
    return _drive_instance
