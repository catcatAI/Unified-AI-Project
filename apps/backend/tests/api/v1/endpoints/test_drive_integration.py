import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import os
import json

# Adjust the path to import main.py correctly
import sys
from os.path import abspath, dirname, join
sys.path.insert(0, abspath(join(dirname(__file__), "..", "..", "..", "..", "..")))

from apps.backend.main import app
client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mocks external dependencies for Google Drive integration tests."""
    # Try both possible paths for patching
    drive_module = "src.api.v1.endpoints.drive"
    main_module = "main"
    
    with patch(f"{main_module}.system_manager") as mock_system_manager, \
         patch(f"{drive_module}.drive_service", autospec=True) as mock_drive_service, \
         patch(f"{drive_module}.DriveDeduplication", autospec=True) as MockDriveDeduplication, \
         patch(f"{drive_module}.DocumentParser", autospec=True) as MockDocumentParser, \
         patch(f"{drive_module}.ham_memory_manager", autospec=True) as mock_ham_memory_manager:

        # Configure mock_system_manager and its components as they are accessed by drive.py globally
        mock_system_manager.google_drive_service = mock_drive_service
        mock_system_manager.ham_memory_manager = mock_ham_memory_manager

        mock_drive_service.is_authenticated.return_value = True
        mock_drive_service.authenticate.return_value = True
        
        # Mock DriveDeduplication methods
        mock_deduplication_instance = MockDriveDeduplication.return_value
        mock_deduplication_instance.should_download.return_value = True
        mock_deduplication_instance.record_sync.return_value = None
        mock_deduplication_instance.compute_content_hash.return_value = "dummy_hash"

        # Mock DocumentParser methods
        mock_document_parser_instance = MockDocumentParser.return_value
        mock_document_parser_instance.parse_document.return_value = "parsed content"

        # Mock HAMMemoryManager methods
        mock_ham_memory_manager.store_experience = AsyncMock(return_value="memory_id_123")

        yield {
            "mock_system_manager": mock_system_manager,
            "mock_drive_service": mock_drive_service,
            "mock_deduplication_instance": mock_deduplication_instance,
            "mock_document_parser_instance": mock_document_parser_instance,
            "mock_ham_memory_manager": mock_ham_memory_manager,
        }

@pytest.fixture
def sample_file_metadata():
    return {
        "id": "file123",
        "name": "document.txt",
        "mimeType": "text/plain",
        "modifiedTime": "2026-01-01T10:00:00Z",
        "size": "1234",
        "webViewLink": "http://example.com/view/file123"
    }

@pytest.mark.asyncio
async def test_sync_files_new_file_success(mock_dependencies, sample_file_metadata):
    """Test successful sync and memorization of a new file."""
    # Ensure local path exists for mock download
    download_folder = Path("data/drive_downloads")
    download_folder.mkdir(parents=True, exist_ok=True)
    
    # Mock download_file to succeed
    mock_dependencies["mock_drive_service"].download_file.return_value = True
    mock_dependencies["mock_drive_service"].get_file_metadata.return_value = sample_file_metadata
    
    response = client.post(
        "/api/v1/drive/files/sync",
        json={"file_ids": ["file123"], "folder_path": str(download_folder)}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["synced"] == 1
    assert data["skipped"] == 0
    assert data["memorized_count"] == 1
    assert data["files"][0]["name"] == "document.txt"
    assert data["files"][0]["memorized"] == True
    
    mock_dependencies["mock_drive_service"].get_file_metadata.assert_called_with("file123")
    mock_dependencies["mock_deduplication_instance"].should_download.assert_called_with(sample_file_metadata)
    mock_dependencies["mock_drive_service"].download_file.assert_called()
    mock_dependencies["mock_deduplication_instance"].record_sync.assert_called()
    mock_dependencies["mock_document_parser_instance"].parse_document.assert_called()
    mock_dependencies["mock_ham_memory_manager"].store_experience.assert_called()

@pytest.mark.asyncio
async def test_sync_files_skip_unchanged_file(mock_dependencies, sample_file_metadata):
    """Test skipping an unchanged file due to deduplication."""
    mock_dependencies["mock_deduplication_instance"].should_download.return_value = False
    mock_dependencies["mock_drive_service"].get_file_metadata.return_value = sample_file_metadata
    
    response = client.post(
        "/api/v1/drive/files/sync",
        json={"file_ids": ["file123"]}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["synced"] == 0
    assert data["skipped"] == 1
    assert data["memorized_count"] == 0
    
    mock_dependencies["mock_deduplication_instance"].should_download.assert_called_with(sample_file_metadata)
    mock_dependencies["mock_drive_service"].download_file.assert_not_called()
    mock_dependencies["mock_ham_memory_manager"].store_experience.assert_not_called()

@pytest.mark.asyncio
async def test_sync_files_download_failure(mock_dependencies, sample_file_metadata):
    """Test handling of a download failure."""
    mock_dependencies["mock_drive_service"].download_file.return_value = False
    mock_dependencies["mock_drive_service"].get_file_metadata.return_value = sample_file_metadata
    
    response = client.post(
        "/api/v1/drive/files/sync",
        json={"file_ids": ["file123"], "folder_path": "data/drive_downloads"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["synced"] == 1
    assert data["memorized_count"] == 0
    assert data["files"][0]["memorized"] == False
    assert data["files"][0]["error"] == "Download failed"
    
    mock_dependencies["mock_drive_service"].download_file.assert_called()
    mock_dependencies["mock_ham_memory_manager"].store_experience.assert_not_called()

@pytest.mark.asyncio
async def test_sync_files_memorize_different_types(mock_dependencies, sample_file_metadata):
    """Test syncing and memorizing different file types (PDF, CSV)."""
    pdf_metadata = {**sample_file_metadata, "id": "pdf456", "name": "report.pdf", "mimeType": "application/pdf"}
    csv_metadata = {**sample_file_metadata, "id": "csv789", "name": "data.csv", "mimeType": "text/csv"}
    
    mock_dependencies["mock_drive_service"].download_file.return_value = True
    mock_dependencies["mock_drive_service"].get_file_metadata.side_effect = [pdf_metadata, csv_metadata]
    mock_dependencies["mock_deduplication_instance"].should_download.return_value = True
    mock_dependencies["mock_document_parser_instance"].parse_document.side_effect = ["PDF content", "CSV content"]
    
    response = client.post(
        "/api/v1/drive/files/sync",
        json={"file_ids": ["pdf456", "csv789"], "folder_path": "data/drive_downloads"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["synced"] == 2
    assert data["memorized_count"] == 2
    
    assert mock_dependencies["mock_ham_memory_manager"].store_experience.call_count == 2
    
    # Check first call (PDF)
    call_args_pdf = mock_dependencies["mock_ham_memory_manager"].store_experience.call_args_list[0].args[0]
    assert call_args_pdf["content"] == "PDF content"
    assert call_args_pdf["metadata"]["file_id"] == "pdf456"
    assert call_args_pdf["metadata"]["mime_type"] == "application/pdf"
    
    # Check second call (CSV)
    call_args_csv = mock_dependencies["mock_ham_memory_manager"].store_experience.call_args_list[1].args[0]
    assert call_args_csv["content"] == "CSV content"
    assert call_args_csv["metadata"]["file_id"] == "csv789"
    assert call_args_csv["metadata"]["mime_type"] == "text/csv"

# You might want to add tests for authentication failures,
# or when ham_memory_manager is not initialized (503 status).
# These would be similar to other endpoints in the API tests.
