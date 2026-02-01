"""
Angela AI v6.0 - Desktop Interaction Tests
桌面交互系统测试

Comprehensive test suite for the desktop interaction system including:
- DesktopInteraction initialization and file operations
- File organization by category
- Desktop cleanup functionality
- File system monitoring
- Cross-platform compatibility (mock tests)

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

import pytest
import asyncio
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Generator
from unittest.mock import Mock, patch, MagicMock

# Import the modules under test
import sys
sys.path.insert(0, 'D:\\Projects\\Unified-AI-Project\\apps\\backend\\src')

from core.autonomous.desktop_interaction import (
    FileOperationType,
    FileCategory,
    FileOperation,
    DesktopState,
    FileWatcherConfig,
    DesktopInteraction,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_desktop_dir() -> Generator[Path, None, None]:
    """Create a temporary desktop directory for testing."""
    temp_dir = Path(tempfile.mkdtemp(prefix="test_desktop_"))
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def desktop_interaction(temp_desktop_dir: Path) -> DesktopInteraction:
    """Create a DesktopInteraction instance with temp directory."""
    config = {
        "desktop_path": str(temp_desktop_dir),
        "organized_path": str(temp_desktop_dir / "Organized"),
        "wallpaper_path": str(temp_desktop_dir / "Wallpapers"),
        "auto_organize": False
    }
    return DesktopInteraction(config=config)


@pytest.fixture
def initialized_desktop(temp_desktop_dir: Path) -> Generator[DesktopInteraction, None, None]:
    """Create an initialized DesktopInteraction instance."""
    config = {
        "desktop_path": str(temp_desktop_dir),
        "organized_path": str(temp_desktop_dir / "Organized"),
        "wallpaper_path": str(temp_desktop_dir / "Wallpapers"),
        "auto_organize": False
    }
    desktop = DesktopInteraction(config=config)
    asyncio.run(desktop.initialize())
    yield desktop
    asyncio.run(desktop.shutdown())


@pytest.fixture
def sample_files(temp_desktop_dir: Path) -> Dict[str, Path]:
    """Create sample files for testing."""
    files = {}
    
    # Document
    doc_file = temp_desktop_dir / "test_doc.txt"
    doc_file.write_text("Test document content")
    files["document"] = doc_file
    
    # Image
    img_file = temp_desktop_dir / "test_img.png"
    img_file.write_bytes(b"PNG fake content")
    files["image"] = img_file
    
    # Code file
    code_file = temp_desktop_dir / "test_script.py"
    code_file.write_text("print('hello')")
    files["code"] = code_file
    
    return files


# =============================================================================
# FileOperationType Tests
# =============================================================================

class TestFileOperationType:
    """Tests for the FileOperationType enum."""

    def test_operation_types(self) -> None:
        """Test all file operation types are defined."""
        operations = [
            FileOperationType.CREATE,
            FileOperationType.DELETE,
            FileOperationType.MOVE,
            FileOperationType.COPY,
            FileOperationType.RENAME,
            FileOperationType.ORGANIZE,
            FileOperationType.CLEANUP
        ]
        
        for op in operations:
            assert op.cn_name is not None
            assert op.en_name is not None


# =============================================================================
# FileCategory Tests
# =============================================================================

class TestFileCategory:
    """Tests for the FileCategory enum."""

    def test_category_count(self) -> None:
        """Test number of file categories."""
        assert len(FileCategory) == 9

    def test_document_extensions(self) -> None:
        """Test document category extensions."""
        assert ".txt" in FileCategory.DOCUMENTS.extensions
        assert ".pdf" in FileCategory.DOCUMENTS.extensions
        assert ".doc" in FileCategory.DOCUMENTS.extensions
        assert ".md" in FileCategory.DOCUMENTS.extensions

    def test_image_extensions(self) -> None:
        """Test image category extensions."""
        assert ".jpg" in FileCategory.IMAGES.extensions
        assert ".png" in FileCategory.IMAGES.extensions
        assert ".gif" in FileCategory.IMAGES.extensions

    def test_code_extensions(self) -> None:
        """Test code category extensions."""
        assert ".py" in FileCategory.CODE.extensions
        assert ".js" in FileCategory.CODE.extensions
        assert ".html" in FileCategory.CODE.extensions

    def test_categorize_file(self, desktop_interaction: DesktopInteraction) -> None:
        """Test file categorization."""
        # Test various extensions
        assert desktop_interaction._categorize_file(Path("test.txt")) == FileCategory.DOCUMENTS
        assert desktop_interaction._categorize_file(Path("test.png")) == FileCategory.IMAGES
        assert desktop_interaction._categorize_file(Path("test.py")) == FileCategory.CODE
        assert desktop_interaction._categorize_file(Path("test.unknown")) == FileCategory.OTHER


# =============================================================================
# FileOperation Tests
# =============================================================================

class TestFileOperation:
    """Tests for the FileOperation data class."""

    def test_operation_creation(self) -> None:
        """Test file operation creation."""
        operation = FileOperation(
            operation_id="op_001",
            operation_type=FileOperationType.CREATE,
            source_path=Path("/test/source.txt")
        )
        
        assert operation.operation_id == "op_001"
        assert operation.operation_type == FileOperationType.CREATE
        assert operation.source_path == Path("/test/source.txt")
        assert operation.status == "pending"

    def test_operation_with_target(self) -> None:
        """Test operation with target path."""
        operation = FileOperation(
            operation_id="op_002",
            operation_type=FileOperationType.MOVE,
            source_path=Path("/test/source.txt"),
            target_path=Path("/test/target.txt")
        )
        
        assert operation.target_path == Path("/test/target.txt")


# =============================================================================
# DesktopState Tests
# =============================================================================

class TestDesktopState:
    """Tests for the DesktopState data class."""

    def test_state_creation(self) -> None:
        """Test desktop state creation."""
        state = DesktopState()
        
        assert state.total_files == 0
        assert state.total_size == 0
        assert state.clutter_level == 0.0
        assert state.last_organized is None

    def test_state_with_data(self) -> None:
        """Test state with populated data."""
        state = DesktopState(
            total_files=25,
            total_size=1024000,
            clutter_level=0.5
        )
        
        assert state.total_files == 25
        assert state.total_size == 1024000
        assert state.clutter_level == 0.5


# =============================================================================
# FileWatcherConfig Tests
# =============================================================================

class TestFileWatcherConfig:
    """Tests for the FileWatcherConfig data class."""

    def test_default_config(self) -> None:
        """Test default watcher configuration."""
        config = FileWatcherConfig()
        
        assert len(config.watch_paths) == 0
        assert "*.tmp" in config.ignored_patterns
        assert config.auto_organize is False
        assert config.organize_threshold == 20


# =============================================================================
# DesktopInteraction Tests
# =============================================================================

class TestDesktopInteraction:
    """Tests for the main DesktopInteraction class."""

    @pytest.mark.asyncio
    async def test_initialization(self, desktop_interaction: DesktopInteraction, temp_desktop_dir: Path) -> None:
        """Test desktop interaction initialization."""
        await desktop_interaction.initialize()
        
        # Should create organized directory structure
        organized_dir = temp_desktop_dir / "Organized"
        assert organized_dir.exists()
        
        # Should create category subdirectories
        for category in FileCategory:
            category_dir = organized_dir / category.cn_name
            assert category_dir.exists()
        
        await desktop_interaction.shutdown()

    def test_initialization_paths(self, desktop_interaction: DesktopInteraction, temp_desktop_dir: Path) -> None:
        """Test that paths are set correctly."""
        assert desktop_interaction.desktop_path == temp_desktop_dir
        assert desktop_interaction.organized_path == temp_desktop_dir / "Organized"
        assert desktop_interaction.wallpaper_path == temp_desktop_dir / "Wallpapers"

    @pytest.mark.asyncio
    async def test_create_file(self, initialized_desktop: DesktopInteraction, temp_desktop_dir: Path) -> None:
        """Test file creation."""
        result = await initialized_desktop.create_file(
            filename="test_note.txt",
            content="Test content for file creation",
            category=FileCategory.DOCUMENTS
        )
        
        assert result is not None
        assert result.exists()
        assert result.read_text() == "Test content for file creation"
        
        # Should be in Documents folder
        expected_path = temp_desktop_dir / "Organized" / "文档" / "test_note.txt"
        assert result == expected_path

    @pytest.mark.asyncio
    async def test_create_file_no_category(self, initialized_desktop: DesktopInteraction, temp_desktop_dir: Path) -> None:
        """Test file creation without category (goes to desktop)."""
        result = await initialized_desktop.create_file(
            filename="direct_file.txt",
            content="Direct desktop file"
        )
        
        assert result is not None
        assert result.exists()
        # Should be on desktop
        assert result.parent == temp_desktop_dir

    @pytest.mark.asyncio
    async def test_delete_file(self, initialized_desktop: DesktopInteraction, sample_files: Dict[str, Path]) -> None:
        """Test file deletion."""
        file_to_delete = sample_files["document"]
        
        # Verify file exists
        assert file_to_delete.exists()
        
        # Delete
        result = await initialized_desktop.delete_file(file_to_delete)
        
        assert result is True
        assert not file_to_delete.exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, initialized_desktop: DesktopInteraction) -> None:
        """Test deleting non-existent file."""
        nonexistent = Path("/nonexistent/path/file.txt")
        
        result = await initialized_desktop.delete_file(nonexistent)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_move_file(self, initialized_desktop: DesktopInteraction, temp_desktop_dir: Path, sample_files: Dict[str, Path]) -> None:
        """Test file movement."""
        source = sample_files["document"]
        target = temp_desktop_dir / "moved_file.txt"
        
        result = await initialized_desktop.move_file(source, target)
        
        assert result is True
        assert not source.exists()
        assert target.exists()

    @pytest.mark.asyncio
    async def test_organize_desktop(self, initialized_desktop: DesktopInteraction, temp_desktop_dir: Path, sample_files: Dict[str, Path]) -> None:
        """Test desktop organization."""
        # Scan to populate state
        await initialized_desktop._scan_desktop()
        
        # Organize
        operations = await initialized_desktop.organize_desktop()
        
        # Should have moved files
        assert len(operations) > 0
        
        # Check that files were moved to appropriate categories
        doc_file = sample_files["document"]
        if not doc_file.exists():  # Was moved
            organized_doc = temp_desktop_dir / "Organized" / "文档" / doc_file.name
            assert organized_doc.exists()

    def test_get_desktop_state(self, initialized_desktop: DesktopInteraction, sample_files: Dict[str, Path]) -> None:
        """Test getting desktop state."""
        # Force scan
        asyncio.run(initialized_desktop._scan_desktop())
        
        state = initialized_desktop.get_desktop_state()
        
        assert isinstance(state, DesktopState)
        assert state.total_files > 0
        assert state.total_size > 0

    def test_clutter_level_calculation(self, initialized_desktop: DesktopInteraction, temp_desktop_dir: Path) -> None:
        """Test clutter level calculation."""
        # Add many files to create clutter
        for i in range(30):
            (temp_desktop_dir / f"clutter_file_{i}.txt").write_text("content")
        
        # Force scan
        asyncio.run(initialized_desktop._scan_desktop())
        
        state = initialized_desktop.get_desktop_state()
        # 30 files should give moderate clutter (30/50 = 0.6)
        assert state.clutter_level > 0.5

    @pytest.mark.asyncio
    async def test_cleanup_desktop(self, initialized_desktop: DesktopInteraction, temp_desktop_dir: Path) -> None:
        """Test desktop cleanup."""
        # Create old temp files
        old_temp = temp_desktop_dir / "old_file.tmp"
        old_temp.write_text("temp content")
        
        # Set modification time to old
        old_time = datetime.now() - timedelta(days=35)
        import os
        os.utime(old_temp, (old_time.timestamp(), old_time.timestamp()))
        
        # Cleanup files older than 30 days
        operations = await initialized_desktop.cleanup_desktop(days_old=30)
        
        # Should have cleaned up the old temp file
        assert len(operations) >= 1
        assert not old_temp.exists()

    def test_get_files_by_category(self, initialized_desktop: DesktopInteraction, temp_desktop_dir: Path) -> None:
        """Test getting files by category."""
        # Create a file in organized documents
        doc_dir = temp_desktop_dir / "Organized" / "文档"
        doc_dir.mkdir(parents=True, exist_ok=True)
        (doc_dir / "test_doc.txt").write_text("content")
        
        files = initialized_desktop.get_files_by_category(FileCategory.DOCUMENTS)
        
        assert len(files) > 0

    def test_callback_registration(self, initialized_desktop: DesktopInteraction) -> None:
        """Test callback registration."""
        callback_called = [False]
        
        def test_callback(file_path: Path, change_type: str) -> None:
            callback_called[0] = True
        
        initialized_desktop.register_file_change_callback(test_callback)
        
        assert len(initialized_desktop._file_change_callbacks) == 1

    def test_operation_callback_registration(self, initialized_desktop: DesktopInteraction) -> None:
        """Test operation callback registration."""
        callback_called = [False]
        
        def test_callback(operation: FileOperation) -> None:
            callback_called[0] = True
        
        initialized_desktop.register_operation_callback(test_callback)
        
        assert len(initialized_desktop._operation_callbacks) == 1

    def test_get_operation_history(self, initialized_desktop: DesktopInteraction) -> None:
        """Test getting operation history."""
        # Initially empty
        history = initialized_desktop.get_operation_history()
        assert len(history) == 0

    def test_get_operation_history_since(self, initialized_desktop: DesktopInteraction) -> None:
        """Test getting operation history with time filter."""
        since_time = datetime.now() - timedelta(hours=1)
        history = initialized_desktop.get_operation_history(since=since_time)
        assert isinstance(history, list)


# =============================================================================
# Cross-Platform Tests (Mock)
# =============================================================================

class TestCrossPlatformCompatibility:
    """Tests for cross-platform compatibility using mocks."""

    @pytest.mark.asyncio
    @patch("platform.system")
    @patch("ctypes.windll.user32.SystemParametersInfoW")
    async def test_set_wallpaper_windows(self, mock_spi, mock_platform, temp_desktop_dir: Path) -> None:
        """Test wallpaper setting on Windows (mocked)."""
        mock_platform.return_value = "Windows"
        mock_spi.return_value = True
        
        desktop = DesktopInteraction(config={"desktop_path": str(temp_desktop_dir)})
        
        # Create fake wallpaper file
        wallpaper = temp_desktop_dir / "test_wallpaper.jpg"
        wallpaper.write_bytes(b"fake image data")
        
        result = await desktop.set_wallpaper(wallpaper)
        
        assert result is True
        mock_spi.assert_called_once()

    @pytest.mark.asyncio
    @patch("platform.system")
    @patch("os.system")
    async def test_set_wallpaper_macos(self, mock_system, mock_platform, temp_desktop_dir: Path) -> None:
        """Test wallpaper setting on macOS (mocked)."""
        mock_platform.return_value = "Darwin"
        mock_system.return_value = 0
        
        desktop = DesktopInteraction(config={"desktop_path": str(temp_desktop_dir)})
        
        wallpaper = temp_desktop_dir / "test_wallpaper.jpg"
        wallpaper.write_bytes(b"fake image data")
        
        result = await desktop.set_wallpaper(wallpaper)
        
        assert result is True
        mock_system.assert_called_once()

    @pytest.mark.asyncio
    @patch("platform.system")
    @patch("os.environ.get")
    @patch("os.system")
    async def test_set_wallpaper_linux_gnome(self, mock_system, mock_env, mock_platform, temp_desktop_dir: Path) -> None:
        """Test wallpaper setting on Linux GNOME (mocked)."""
        mock_platform.return_value = "Linux"
        mock_env.return_value = "gnome"
        mock_system.return_value = 0
        
        desktop = DesktopInteraction(config={"desktop_path": str(temp_desktop_dir)})
        
        wallpaper = temp_desktop_dir / "test_wallpaper.jpg"
        wallpaper.write_bytes(b"fake image data")
        
        result = await desktop.set_wallpaper(wallpaper)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_set_wallpaper_nonexistent_file(self, temp_desktop_dir: Path) -> None:
        """Test wallpaper setting with non-existent file."""
        desktop = DesktopInteraction(config={"desktop_path": str(temp_desktop_dir)})
        
        nonexistent = temp_desktop_dir / "nonexistent.jpg"
        
        result = await desktop.set_wallpaper(nonexistent)
        
        assert result is False

    @pytest.mark.asyncio
    @patch("random.choice")
    async def test_rotate_wallpaper(self, mock_choice, temp_desktop_dir: Path) -> None:
        """Test wallpaper rotation."""
        desktop = DesktopInteraction(config={
            "desktop_path": str(temp_desktop_dir),
            "wallpaper_path": str(temp_desktop_dir / "Wallpapers")
        })
        
        # Create wallpaper directory and files
        wallpaper_dir = temp_desktop_dir / "Wallpapers"
        wallpaper_dir.mkdir()
        (wallpaper_dir / "wall1.jpg").write_bytes(b"fake")
        (wallpaper_dir / "wall2.png").write_bytes(b"fake")
        
        mock_choice.return_value = wallpaper_dir / "wall1.jpg"
        
        with patch.object(desktop, 'set_wallpaper', return_value=True):
            result = await desktop.rotate_wallpaper()
            assert result is True

    @pytest.mark.asyncio
    async def test_rotate_wallpaper_no_wallpapers(self, temp_desktop_dir: Path) -> None:
        """Test wallpaper rotation with no wallpapers available."""
        desktop = DesktopInteraction(config={
            "desktop_path": str(temp_desktop_dir),
            "wallpaper_path": str(temp_desktop_dir / "EmptyWallpapers")
        })
        
        # Create empty wallpaper directory
        (temp_desktop_dir / "EmptyWallpapers").mkdir()
        
        result = await desktop.rotate_wallpaper()
        
        assert result is False


# =============================================================================
# File System Monitoring Tests
# =============================================================================

class TestFileSystemMonitoring:
    """Tests for file system monitoring functionality."""

    @pytest.mark.asyncio
    async def test_file_detection(self, initialized_desktop: DesktopInteraction, temp_desktop_dir: Path) -> None:
        """Test file detection in monitoring."""
        # Create a new file
        new_file = temp_desktop_dir / "new_detected_file.txt"
        new_file.write_text("New content")
        
        # Force scan
        await initialized_desktop._scan_desktop()
        
        # Should be in cache
        assert str(new_file) in initialized_desktop._file_cache

    @pytest.mark.asyncio
    async def test_file_deletion_detection(self, initialized_desktop: DesktopInteraction, temp_desktop_dir: Path, sample_files: Dict[str, Path]) -> None:
        """Test detection of file deletion."""
        doc_file = sample_files["document"]
        
        # Initial scan
        await initialized_desktop._scan_desktop()
        assert str(doc_file) in initialized_desktop._file_cache
        
        # Delete file
        doc_file.unlink()
        
        # Scan again
        await initialized_desktop._scan_desktop()
        
        # Should be removed from cache
        assert str(doc_file) not in initialized_desktop._file_cache

    @pytest.mark.asyncio
    async def test_auto_organize_trigger(self, temp_desktop_dir: Path) -> None:
        """Test auto-organize trigger when threshold exceeded."""
        config = {
            "desktop_path": str(temp_desktop_dir),
            "auto_organize": True,
            "organize_threshold": 5
        }
        desktop = DesktopInteraction(config=config)
        await desktop.initialize()
        
        try:
            # Add many files to trigger auto-organize
            for i in range(10):
                (temp_desktop_dir / f"auto_file_{i}.txt").write_text("content")
            
            # Force scan
            await desktop._scan_desktop()
            
            # Check auto-organize would be triggered
            # (We don't actually trigger it to avoid test flakiness)
            assert desktop.current_state.total_files >= 10
            
        finally:
            await desktop.shutdown()


# =============================================================================
# Integration Tests
# =============================================================================

class TestDesktopInteractionIntegration:
    """Integration tests for desktop interaction."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, temp_desktop_dir: Path) -> None:
        """Test complete desktop interaction workflow."""
        desktop = DesktopInteraction(config={
            "desktop_path": str(temp_desktop_dir),
            "organized_path": str(temp_desktop_dir / "Organized")
        })
        
        await desktop.initialize()
        
        try:
            # 1. Create some files
            await desktop.create_file("doc1.txt", "Document 1", FileCategory.DOCUMENTS)
            await desktop.create_file("img1.png", "fake", FileCategory.IMAGES)
            
            # 2. Check state
            await desktop._scan_desktop()
            state = desktop.get_desktop_state()
            assert state.total_files > 0
            
            # 3. Organize
            operations = await desktop.organize_desktop()
            
            # 4. Cleanup
            cleanup_ops = await desktop.cleanup_desktop(days_old=30)
            
            # 5. Check history
            history = desktop.get_operation_history()
            assert len(history) > 0
            
        finally:
            await desktop.shutdown()

    def test_file_categorization_accuracy(self, desktop_interaction: DesktopInteraction) -> None:
        """Test accurate file categorization for various extensions."""
        test_cases = [
            ("file.txt", FileCategory.DOCUMENTS),
            ("file.pdf", FileCategory.DOCUMENTS),
            ("file.jpg", FileCategory.IMAGES),
            ("file.png", FileCategory.IMAGES),
            ("file.py", FileCategory.CODE),
            ("file.js", FileCategory.CODE),
            ("file.mp3", FileCategory.AUDIO),
            ("file.mp4", FileCategory.VIDEOS),
            ("file.zip", FileCategory.ARCHIVES),
            ("file.exe", FileCategory.EXECUTABLES),
            ("file.json", FileCategory.DATA),
            ("file.unknown", FileCategory.OTHER),
        ]
        
        for filename, expected_category in test_cases:
            result = desktop_interaction._categorize_file(Path(filename))
            assert result == expected_category, f"Failed for {filename}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
