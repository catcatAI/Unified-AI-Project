import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import os
import json

from apps.backend.src.services.main_api_server import app
from apps.backend.src.api.v1.endpoints._deps import get_drive_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mocks external dependencies for Google Drive integration tests."""
    drive_module = "api.v1.endpoints.drive"

    mock_drive_service = MagicMock()
    mock_drive_service.is_authenticated.return_value = True
    mock_drive_service.authenticate.return_value = True
    app.dependency_overrides[get_drive_service] = lambda: mock_drive_service

    mock_ham = MagicMock()
    mock_ham.store_conversation = MagicMock()

    with patch("ai.memory.ham_memory.ham_manager.HAMMemoryManager", return_value=mock_ham), \
         patch(f"{drive_module}.DriveDeduplication") as MockDriveDeduplication, \
         patch(f"{drive_module}.DocumentParser") as MockDocumentParser:

        mock_deduplication_instance = MockDriveDeduplication.return_value
        mock_deduplication_instance.should_download.return_value = True
        mock_deduplication_instance.record_sync.return_value = None
        mock_deduplication_instance.compute_content_hash.return_value = "dummy_hash"

        mock_document_parser_instance = MockDocumentParser.return_value
        mock_document_parser_instance.parse_document.return_value = "parsed content"

        yield {
            "mock_drive_service": mock_drive_service,
            "mock_deduplication_instance": mock_deduplication_instance,
            "mock_document_parser_instance": mock_document_parser_instance,
            "mock_ham": mock_ham,
        }

    app.dependency_overrides.pop(get_drive_service, None)


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


def test_sync_files_new_file_success(mock_dependencies, sample_file_metadata):
    """Test successful sync and memorization of a new file."""
    mock_svc = mock_dependencies["mock_drive_service"]
    mock_svc.download_file.return_value = True
    mock_svc.get_file_metadata.return_value = sample_file_metadata

    with tempfile.TemporaryDirectory() as tmpdir:
        response = client.post(
            "/api/v1/drive/files/sync",
            json={"file_ids": ["file123"], "folder_path": tmpdir}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["synced"] == 1
    assert data["skipped"] == 0
    assert data["memorized_count"] == 1
    assert data["files"][0]["name"] == "document.txt"
    assert data["files"][0]["memorized"] == True

    mock_svc.get_file_metadata.assert_called_with("file123")
    mock_dependencies["mock_deduplication_instance"].should_download.assert_called_with(sample_file_metadata)
    mock_svc.download_file.assert_called()
    mock_dependencies["mock_deduplication_instance"].record_sync.assert_called()
    mock_dependencies["mock_document_parser_instance"].parse_document.assert_called()
    mock_dependencies["mock_ham"].store_conversation.assert_called()


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
    mock_dependencies["mock_ham"].store_conversation.assert_not_called()


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
    assert data["synced"] == 0
    assert data["memorized_count"] == 0
    assert data["files"][0]["memorized"] == False
    assert data["files"][0]["error"] == "Download failed"

    mock_dependencies["mock_drive_service"].download_file.assert_called()
    mock_dependencies["mock_ham"].store_conversation.assert_not_called()


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

    assert mock_dependencies["mock_ham"].store_conversation.call_count == 2
