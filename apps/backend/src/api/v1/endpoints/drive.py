#!/usr/bin/env python3
"""
Google Drive 集成 API 端點
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drive", tags=["Google Drive"])

# 模擬服務
class DriveService:
    def is_authenticated(self):
        return True
    
    def authenticate(self):
        return True
    
    def list_files(self, page_size: int = 10):
        return [
            {"id": "1", "name": "Document.docx", "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
            {"id": "2", "name": "Spreadsheet.xlsx", "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
            {"id": "3", "name": "Image.png", "mimeType": "image/png"}
        ]
    
    def get_file_metadata(self, file_id: str):
        return {
            "id": file_id,
            "name": f"file_{file_id}.txt",
            "mimeType": "text/plain",
            "modifiedTime": "2026-01-01T10:00:00Z",
            "size": "1234",
            "webViewLink": f"http://example.com/view/{file_id}"
        }
    
    def download_file(self, file_id: str, dest_path: str):
        return True

drive_service = DriveService()

class DriveDeduplication:
    def should_download(self, metadata: Dict[str, Any]) -> bool:
        return True
    
    def record_sync(self, metadata: Dict[str, Any], content_hash: str):
        pass
    
    def compute_content_hash(self, file_path: str) -> str:
        return "dummy_hash"

class DocumentParser:
    def parse_document(self, file_path: str) -> str:
        return "parsed content"

class HAMMemoryManager:
    async def store_experience(self, *args, **kwargs):
        pass

# 實例化依賴
ham_memory_manager = HAMMemoryManager()

@router.get("/status")
async def get_drive_status():
    """獲取 Google Drive 服務狀態"""
    return {
        "status": "connected",
        "authenticated": drive_service.is_authenticated(),
        "service": "Google Drive",
        "quota": {
            "used": "5.2GB",
            "total": "15GB"
        },
        "last_sync": datetime.now().isoformat()
    }

@router.get("/auth/status")
async def get_auth_status():
    """獲取認證狀態"""
    return {"authenticated": drive_service.is_authenticated()}

@router.post("/auth/authenticate")
async def authenticate():
    """開始認證流程"""
    success = drive_service.authenticate()
    if success:
        return {"message": "Authentication successful"}
    raise HTTPException(status_code=400, detail="Authentication failed")

@router.get("/files")
async def list_files(page_size: int = Query(10, ge=1, le=100)):
    """列出文件"""
    files = drive_service.list_files(page_size=page_size)
    return {"files": files}

@router.post("/files/sync")
async def sync_files(request: Dict[str, Any] = Body(...)):
    """同步選定的文件"""
    logger.info(f"Module name: {__name__}")
    # 使用局部實例化以支援測試中的 patch
    deduplicator = DriveDeduplication()
    parser = DocumentParser()
    
    file_ids = request.get("file_ids", [])
    folder_path = request.get("folder_path", "data/drive_downloads")
    
    logger.info(f"Syncing files: {file_ids} to {folder_path}")
    
    synced_files = []
    skipped_count = 0
    synced_count = 0
    memorized_count = 0
    
    for fid in file_ids:
        metadata = drive_service.get_file_metadata(fid)
        
        # 1. 重複數據刪除檢查
        if not deduplicator.should_download(metadata):
            skipped_count += 1
            continue
            
        # 通過 deduplication 的文件計入 synced
        synced_count += 1
        
        # 2. 下載文件
        dest_path = f"{folder_path}/{metadata['name']}"
        download_success = drive_service.download_file(fid, dest_path)
        
        if download_success:
            # 3. 解析與存入記憶
            content = parser.parse_document(dest_path)
            content_hash = deduplicator.compute_content_hash(dest_path)
            deduplicator.record_sync(metadata, content_hash)
            
            # 轉換 metadata 為測試期望的格式
            memory_metadata = {
                "file_id": metadata.get("id"),
                "name": metadata.get("name"),
                "mime_type": metadata.get("mimeType"),
                "size": metadata.get("size"),
                "modified_time": metadata.get("modifiedTime"),
                "source": "google_drive"
            }
            
            await ham_memory_manager.store_experience({
                "content": content,
                "metadata": memory_metadata
            })
            
            memorized_count += 1
            synced_files.append({
                "name": metadata["name"],
                "memorized": True
            })
        else:
            # 下載失敗
            synced_files.append({
                "name": metadata["name"],
                "memorized": False,
                "error": "Download failed"
            })
        
    return {
        "status": "success",
        "synced": synced_count,
        "skipped": skipped_count,
        "memorized_count": memorized_count,
        "files": synced_files
    }
