"""
Angela AI v6.0 - Desktop Interaction System
桌面交互系统

Manages desktop file operations, file system monitoring, desktop cleanup,
and wallpaper management for Angela AI.

Features:
- Desktop file operations (organize, create, delete)
- File system monitoring and watching
- Automated desktop cleanup
- Wallpaper management and rotation

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import os
import shutil
import json


class FileOperationType(Enum):
    """文件操作类型 / File operation types"""
    CREATE = ("创建", "Create")
    DELETE = ("删除", "Delete")
    MOVE = ("移动", "Move")
    COPY = ("复制", "Copy")
    RENAME = ("重命名", "Rename")
    ORGANIZE = ("整理", "Organize")
    CLEANUP = ("清理", "Cleanup")
    
    def __init__(self, cn_name: str, en_name: str):
        self.cn_name = cn_name
        self.en_name = en_name


class FileCategory(Enum):
    """文件分类 / File categories"""
    DOCUMENTS = ("文档", [".txt", ".doc", ".docx", ".pdf", ".md", ".rtf"])
    IMAGES = ("图片", [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"])
    VIDEOS = ("视频", [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"])
    AUDIO = ("音频", [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"])
    ARCHIVES = ("压缩包", [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"])
    CODE = ("代码", [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".h"])
    EXECUTABLES = ("程序", [".exe", ".msi", ".app", ".deb", ".rpm"])
    DATA = ("数据", [".json", ".xml", ".csv", ".xlsx", ".db", ".sql"])
    OTHER = ("其他", [])
    
    def __init__(self, cn_name: str, extensions: List[str]):
        self.cn_name = cn_name
        self.extensions = extensions


@dataclass
class FileOperation:
    """文件操作 / File operation"""
    operation_id: str
    operation_type: FileOperationType
    source_path: Path
    target_path: Optional[Path] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None


@dataclass
class DesktopState:
    """桌面状态 / Desktop state"""
    total_files: int = 0
    total_size: int = 0  # bytes
    files_by_category: Dict[FileCategory, int] = field(default_factory=dict)
    last_organized: Optional[datetime] = None
    clutter_level: float = 0.0  # 0-1, higher = more cluttered


@dataclass
class FileWatcherConfig:
    """文件监控配置 / File watcher configuration"""
    watch_paths: List[Path] = field(default_factory=list)
    ignored_patterns: List[str] = field(default_factory=lambda: ["*.tmp", "*.log", ".*"])
    auto_organize: bool = False
    organize_threshold: int = 20  # Auto-organize when more than N files


class DesktopInteraction:
    """
    桌面交互系统主类 / Main desktop interaction class
    
    Manages desktop file operations, monitoring, and organization for Angela AI.
    Provides automated cleanup, wallpaper management, and file system monitoring.
    
    Attributes:
        desktop_path: Path to desktop directory
        organized_path: Path for organized files
        current_state: Current desktop state
        watcher_config: File watcher configuration
        operation_history: History of file operations
    
    Example:
        >>> desktop = DesktopInteraction()
        >>> await desktop.initialize()
        >>> 
        >>> # Get desktop state
        >>> state = await desktop.get_desktop_state()
        >>> print(f"Files: {state.total_files}, Clutter: {state.clutter_level:.2f}")
        >>> 
        >>> # Organize desktop
        >>> operations = await desktop.organize_desktop()
        >>> print(f"Organized {len(operations)} files")
        >>> 
        >>> # Set wallpaper
        >>> await desktop.set_wallpaper(Path("~/wallpapers/nature.jpg"))
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Paths
        self.desktop_path = Path(self.config.get("desktop_path", "~/Desktop")).expanduser()
        self.organized_path = Path(self.config.get("organized_path", "~/Desktop/Organized")).expanduser()
        self.wallpaper_path = Path(self.config.get("wallpaper_path", "~/Wallpapers")).expanduser()
        
        # State
        self.current_state: DesktopState = DesktopState()
        self.watcher_config: FileWatcherConfig = FileWatcherConfig(
            watch_paths=[self.desktop_path],
            auto_organize=self.config.get("auto_organize", False)
        )
        
        # Tracking
        self.operation_history: List[FileOperation] = []
        self._file_cache: Dict[str, Dict[str, Any]] = {}
        self._watched_files: Set[str] = set()
        
        # Running state
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._file_change_callbacks: List[Callable[[Path, str], None]] = []
        self._operation_callbacks: List[Callable[[FileOperation], None]] = []
    
    async def initialize(self):
        """Initialize the desktop interaction system"""
        self._running = True
        
        # Ensure organized directory exists
        self.organized_path.mkdir(parents=True, exist_ok=True)
        
        # Create category subdirectories
        for category in FileCategory:
            (self.organized_path / category.cn_name).mkdir(exist_ok=True)
        
        # Initial scan
        await self._scan_desktop()
        
        # Start monitoring
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def shutdown(self):
        """Shutdown the system"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self._running:
            await self._scan_desktop()
            await self._check_auto_organize()
            await asyncio.sleep(30)  # Scan every 30 seconds
    
    async def _scan_desktop(self):
        """Scan desktop and update state"""
        if not self.desktop_path.exists():
            return
        
        current_files = set()
        files_by_category = {cat: 0 for cat in FileCategory}
        total_size = 0
        
        for file_path in self.desktop_path.iterdir():
            if file_path.is_file():
                file_str = str(file_path)
                current_files.add(file_str)
                
                # Check for new or modified files
                if file_str not in self._file_cache:
                    self._notify_file_change(file_path, "created")
                
                # Categorize
                category = self._categorize_file(file_path)
                files_by_category[category] += 1
                
                # Get size
                try:
                    total_size += file_path.stat().st_size
                except:
                    pass
                
                # Update cache
                self._file_cache[file_str] = {
                    "size": total_size,
                    "mtime": file_path.stat().st_mtime
                }
        
        # Check for deleted files
        for cached_file in list(self._file_cache.keys()):
            if cached_file not in current_files:
                self._notify_file_change(Path(cached_file), "deleted")
                del self._file_cache[cached_file]
        
        # Update state
        self.current_state.total_files = len(current_files)
        self.current_state.total_size = total_size
        self.current_state.files_by_category = files_by_category
        
        # Calculate clutter level
        self.current_state.clutter_level = min(1.0, len(current_files) / 50.0)
    
    def _categorize_file(self, file_path: Path) -> FileCategory:
        """Categorize a file by extension"""
        ext = file_path.suffix.lower()
        
        for category in FileCategory:
            if ext in category.extensions:
                return category
        
        return FileCategory.OTHER
    
    def _notify_file_change(self, file_path: Path, change_type: str):
        """Notify file change callbacks"""
        for callback in self._file_change_callbacks:
            try:
                callback(file_path, change_type)
            except Exception:
                pass
    
    async def _check_auto_organize(self):
        """Check if auto-organization is needed"""
        if self.watcher_config.auto_organize:
            if self.current_state.total_files > self.watcher_config.organize_threshold:
                if self.current_state.clutter_level > 0.5:
                    await self.organize_desktop()
    
    async def organize_desktop(self) -> List[FileOperation]:
        """
        Organize desktop files by category
        
        Returns:
            List of file operations performed
        """
        operations = []
        
        if not self.desktop_path.exists():
            return operations
        
        for file_path in self.desktop_path.iterdir():
            if file_path.is_file() and file_path != self.organized_path:
                category = self._categorize_file(file_path)
                target_dir = self.organized_path / category.cn_name
                
                # Generate unique filename if needed
                target_path = target_dir / file_path.name
                counter = 1
                while target_path.exists():
                    target_path = target_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
                    counter += 1
                
                # Perform move operation
                try:
                    operation = FileOperation(
                        operation_id=f"org_{datetime.now().timestamp()}",
                        operation_type=FileOperationType.MOVE,
                        source_path=file_path,
                        target_path=target_path,
                        status="in_progress"
                    )
                    
                    shutil.move(str(file_path), str(target_path))
                    
                    operation.status = "completed"
                    operations.append(operation)
                    self.operation_history.append(operation)
                    
                    # Notify
                    for callback in self._operation_callbacks:
                        try:
                            callback(operation)
                        except Exception:
                            pass
                    
                except Exception as e:
                    operation = FileOperation(
                        operation_id=f"org_{datetime.now().timestamp()}",
                        operation_type=FileOperationType.MOVE,
                        source_path=file_path,
                        status="failed",
                        error_message=str(e)
                    )
                    operations.append(operation)
        
        if operations:
            self.current_state.last_organized = datetime.now()
        
        return operations
    
    async def cleanup_desktop(self, days_old: int = 30) -> List[FileOperation]:
        """
        Clean up old temporary files from desktop
        
        Args:
            days_old: Remove files older than this many days
            
        Returns:
            List of cleanup operations
        """
        operations = []
        cutoff_time = datetime.now() - timedelta(days=days_old)
        
        temp_patterns = ['.tmp', '.temp', '.log', 'cache']
        
        for file_path in self.desktop_path.iterdir():
            if file_path.is_file():
                # Check if it's a temp file
                is_temp = any(pattern in file_path.name.lower() for pattern in temp_patterns)
                
                if is_temp:
                    try:
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if mtime < cutoff_time:
                            operation = FileOperation(
                                operation_id=f"clean_{datetime.now().timestamp()}",
                                operation_type=FileOperationType.DELETE,
                                source_path=file_path,
                                status="in_progress"
                            )
                            
                            file_path.unlink()
                            
                            operation.status = "completed"
                            operations.append(operation)
                            self.operation_history.append(operation)
                    except Exception as e:
                        pass
        
        return operations
    
    async def create_file(
        self, 
        filename: str, 
        content: str, 
        category: Optional[FileCategory] = None
    ) -> Optional[Path]:
        """
        Create a new file on desktop
        
        Args:
            filename: Name of the file
            content: File content
            category: Optional category for organization
            
        Returns:
            Path to created file or None if failed
        """
        try:
            if category:
                target_dir = self.organized_path / category.cn_name
                target_dir.mkdir(parents=True, exist_ok=True)
                file_path = target_dir / filename
            else:
                file_path = self.desktop_path / filename
            
            file_path.write_text(content, encoding='utf-8')
            
            operation = FileOperation(
                operation_id=f"create_{datetime.now().timestamp()}",
                operation_type=FileOperationType.CREATE,
                source_path=file_path,
                status="completed"
            )
            self.operation_history.append(operation)
            
            return file_path
            
        except Exception as e:
            return None
    
    async def delete_file(self, file_path: Path) -> bool:
        """Delete a file"""
        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                
                operation = FileOperation(
                    operation_id=f"delete_{datetime.now().timestamp()}",
                    operation_type=FileOperationType.DELETE,
                    source_path=file_path,
                    status="completed"
                )
                self.operation_history.append(operation)
                
                return True
        except Exception:
            pass
        
        return False
    
    async def move_file(self, source: Path, target: Path) -> bool:
        """Move a file"""
        try:
            if source.exists():
                shutil.move(str(source), str(target))
                return True
        except Exception:
            pass
        return False
    
    async def set_wallpaper(self, image_path: Path) -> bool:
        """
        Set desktop wallpaper
        
        Args:
            image_path: Path to wallpaper image
            
        Returns:
            True if successful
        """
        try:
            if not image_path.exists():
                return False
            
            # Platform-specific wallpaper setting
            import platform
            system = platform.system()
            
            if system == "Windows":
                import ctypes
                SPI_SETDESKWALLPAPER = 20
                ctypes.windll.user32.SystemParametersInfoW(  # type: ignore[attr-defined]
                    SPI_SETDESKWALLPAPER, 0, str(image_path.absolute()), 3
                )
                return True
                
            elif system == "Darwin":  # macOS
                script = f'tell application "Finder" to set desktop picture to POSIX file "{image_path.absolute()}"'
                os.system(f"osascript -e '{script}'")
                return True
                
            elif system == "Linux":
                # Try various desktop environments
                de = os.environ.get("DESKTOP_SESSION", "").lower()
                if "gnome" in de or "unity" in de:
                    os.system(f"gsettings set org.gnome.desktop.background picture-uri file://{image_path.absolute()}")
                elif "kde" in de:
                    os.system(f"qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'var allDesktops = desktops(); for (i=0;i<allDesktops.length;i++) {{ d = allDesktops[i]; d.wallpaperPlugin = \"org.kde.image\"; d.currentConfigGroup = Array(\"Wallpaper\", \"org.kde.image\", \"General\"); d.writeConfig(\"Image\", \"file://{image_path.absolute()}\") }}'")
                return True
                
        except Exception:
            pass
        
        return False
    
    async def rotate_wallpaper(self) -> bool:
        """Rotate to next wallpaper from wallpaper directory"""
        try:
            if not self.wallpaper_path.exists():
                return False
            
            wallpapers = list(self.wallpaper_path.glob("*.jpg")) + \
                        list(self.wallpaper_path.glob("*.png")) + \
                        list(self.wallpaper_path.glob("*.jpeg"))
            
            if wallpapers:
                import random
                next_wallpaper = random.choice(wallpapers)
                return await self.set_wallpaper(next_wallpaper)
                
        except Exception:
            pass
        
        return False
    
    def get_desktop_state(self) -> DesktopState:
        """Get current desktop state"""
        return self.current_state
    
    def get_files_by_category(self, category: FileCategory) -> List[Path]:
        """Get all files of a specific category"""
        files = []
        target_dir = self.organized_path / category.cn_name
        
        if target_dir.exists():
            files = list(target_dir.iterdir())
        
        return files
    
    def register_file_change_callback(self, callback: Callable[[Path, str], None]):
        """Register callback for file changes"""
        self._file_change_callbacks.append(callback)
    
    def register_operation_callback(self, callback: Callable[[FileOperation], None]):
        """Register callback for file operations"""
        self._operation_callbacks.append(callback)
    
    def get_operation_history(
        self, 
        since: Optional[datetime] = None
    ) -> List[FileOperation]:
        """Get operation history"""
        if since is None:
            return self.operation_history.copy()
        
        return [op for op in self.operation_history if op.timestamp > since]


# Example usage
if __name__ == "__main__":
    async def demo():
        desktop = DesktopInteraction()
        await desktop.initialize()
        
        print("=" * 60)
        print("Angela AI v6.0 - 桌面交互系统演示")
        print("Desktop Interaction System Demo")
        print("=" * 60)
        
        # Get state
        print("\n桌面状态 / Desktop state:")
        state = desktop.get_desktop_state()
        print(f"  总文件数: {state.total_files}")
        print(f"  总大小: {state.total_size / 1024 / 1024:.2f} MB")
        print(f"  杂乱度: {state.clutter_level:.2f}")
        
        print("\n按类别分布 / Distribution by category:")
        for cat, count in state.files_by_category.items():
            if count > 0:
                print(f"  {cat.cn_name}: {count}")
        
        # Create test file
        print("\n创建测试文件 / Creating test file:")
        test_file = await desktop.create_file(
            "test_note.txt",
            "This is a test file created by Angela AI",
            category=FileCategory.DOCUMENTS
        )
        if test_file:
            print(f"  Created: {test_file}")
        
        # Cleanup demo
        print("\n清理演示 / Cleanup demo:")
        operations = await desktop.cleanup_desktop(days_old=7)
        print(f"  Cleaned {len(operations)} files")
        
        await desktop.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
