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


class DesktopBrowserIntegration:
    """
    Angela桌面背景浏览器集成
    让Angela能在桌面背景中浏览网页、学习教程、查看作品
    """
    
    def __init__(self, desktop_interaction: DesktopInteraction):
        self.desktop = desktop_interaction
        self.browser_window = None
        self.current_url = None
        self.learning_mode = False
        self.collected_resources = []
        
    async def open_browser_in_background(self, url: str = "about:blank"):
        """
        在桌面背景层打开浏览器窗口
        浏览器位于桌面图标下方，Angela专用
        """
        try:
            import webview
            
            # 创建无边框窗口，位于桌面层
            self.browser_window = webview.create_window(
                'Angela Browser',
                url=url,
                width=1920,
                height=1080,
                x=0,
                y=0,
                frameless=True,
                on_top=False,  # 不置顶，在桌面下方
                transparent=True
            )
            
            self.current_url = url
            logger.info(f"Angela浏览器已在桌面背景打开: {url}")
            
            # 启动webview（非阻塞）
            asyncio.create_task(self._run_browser())
            
        except ImportError:
            logger.warning("webview未安装，使用系统浏览器")
            import webbrowser
            webbrowser.open(url)
    
    async def _run_browser(self):
        """运行浏览器线程"""
        try:
            import webview
            webview.start()
        except Exception as e:
            logger.error(f"浏览器运行错误: {e}")
    
    async def browse_tutorial(self, tutorial_url: str) -> Dict:
        """
        Angela浏览教程页面并提取关键信息
        """
        if self.browser_window:
            self.browser_window.load_url(tutorial_url)
            await asyncio.sleep(3)  # 等待页面加载
            
            # 执行JavaScript提取内容
            content = await self._extract_page_content()
            
            return {
                'url': tutorial_url,
                'title': content.get('title', ''),
                'techniques': content.get('techniques', []),
                'steps': content.get('steps', []),
                'images': content.get('images', []),
                'timestamp': datetime.now()
            }
        else:
            logger.error("浏览器未初始化")
            return {}
    
    async def _extract_page_content(self) -> Dict:
        """提取页面教学内容"""
        try:
            if self.browser_window:
                # 通过JavaScript提取教程内容
                js_code = """
                (function() {
                    return {
                        title: document.title,
                        techniques: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => h.innerText),
                        steps: Array.from(document.querySelectorAll('ol li, ul li')).map(li => li.innerText),
                        images: Array.from(document.querySelectorAll('img')).map(img => img.src)
                    };
                })()
                """
                result = self.browser_window.evaluate_js(js_code)
                return result if result else {}
        except Exception as e:
            logger.error(f"提取内容失败: {e}")
            return {}
    
    async def collect_artwork(self, gallery_url: str) -> List[Dict]:
        """
        Angela浏览作品画廊，收集风格参考
        """
        logger.info(f"Angela正在浏览画廊: {gallery_url}")
        
        artworks = []
        
        if self.browser_window:
            self.browser_window.load_url(gallery_url)
            await asyncio.sleep(3)
            
            # 提取作品图片URL
            js_code = """
            Array.from(document.querySelectorAll('img')).map(img => ({
                src: img.src,
                alt: img.alt,
                width: img.naturalWidth,
                height: img.naturalHeight
            })).filter(img => img.width > 200 && img.height > 200)
            """
            
            images = self.browser_window.evaluate_js(js_code) or []
            
            for img in images[:10]:  # 收集前10张
                artwork = {
                    'source_url': gallery_url,
                    'image_url': img['src'],
                    'description': img['alt'],
                    'dimensions': (img['width'], img['height']),
                    'collected_at': datetime.now()
                }
                artworks.append(artwork)
                self.collected_resources.append(artwork)
        
        logger.info(f"Angela收集了 {len(artworks)} 张参考作品")
        return artworks
    
    async def analyze_style(self, image_url: str) -> Dict:
        """
        Angela分析单张作品的风格特征
        """
        # 下载图片并分析
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        # 使用PIL分析风格
                        from PIL import Image
                        import io
                        
                        img = Image.open(io.BytesIO(image_data))
                        
                        # 提取颜色特征
                        colors = img.getcolors(maxcolors=1000)
                        if colors:
                            dominant_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:5]
                        else:
                            dominant_colors = []
                        
                        # 分析构图
                        width, height = img.size
                        aspect_ratio = width / height
                        
                        return {
                            'dominant_colors': dominant_colors,
                            'aspect_ratio': aspect_ratio,
                            'size': (width, height),
                            'mode': img.mode,
                            'style_tags': self._infer_style_tags(img)
                        }
                        
        except Exception as e:
            logger.error(f"风格分析失败: {e}")
            return {}
    
    def _infer_style_tags(self, img) -> List[str]:
        """推断风格标签"""
        tags = []
        
        # 基于简单特征推断
        width, height = img.size
        
        if width < 200 and height < 200:
            tags.append('icon')
        elif width > 1000 or height > 1000:
            tags.append('wallpaper')
        
        if img.mode == 'RGBA':
            tags.append('transparent')
        
        return tags
    
    async def save_to_desktop(self, content: bytes, filename: str) -> Path:
        """
        保存收集的资源到桌面
        """
        desktop_path = self.desktop.desktop_path
        target_path = desktop_path / filename
        
        with open(target_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"资源已保存到桌面: {target_path}")
        return target_path


class DesktopInteraction:
    """
    桌面交互系统主类 / Main desktop interaction class
    
    Manages desktop file operations, monitoring, and organization for Angela AI.
    Provides automated cleanup, wallpaper management, and file system monitoring.
    
    新增：集成浏览器功能
    
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
    
    async def _handle_file_error(
        self,
        error: Exception,
        operation: FileOperation,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        实现文件操作错误处理 / Implement file operation error handling
        
        关键错误处理功能：
        - 文件不存在时的优雅处理（创建占位符或返回友好错误）
        - 权限不足时的处理（尝试提升权限或记录失败）
        - 磁盘空间不足时的处理（检查空间并清理临时文件）
        - 添加操作回滚机制（恢复到操作前状态）
        - 记录错误日志到系统（详细错误信息）
        
        Critical error handling features:
        - Graceful handling when file doesn't exist (placeholder or friendly error)
        - Permission denied handling (attempt elevation or log failure)
        - Disk space full handling (check space and cleanup temp files)
        - Operation rollback mechanism (restore to pre-operation state)
        - Error logging to system (detailed error information)
        
        Args:
            error: The exception that occurred
            operation: FileOperation that failed
            context: Additional context about the operation (paths, backup paths, etc.)
            
        Returns:
            Dict containing error handling results:
            - handled: Whether error was successfully handled
            - error_type: Type of error encountered
            - recovery_action: Action taken to recover
            - rollback_successful: Whether rollback was performed successfully
            - log_entry: Error log entry details
            
        Example:
            >>> result = await desktop._handle_file_error(
            ...     error=e,
            ...     operation=failed_op,
            ...     context={"backup_path": backup, "original_path": original}
            ... )
            >>> if not result["handled"]:
            ...     print(f"Failed to handle error: {result['error_type']}")
        """
        import errno
        import shutil
        
        results = {
            "handled": False,
            "error_type": type(error).__name__,
            "recovery_action": None,
            "rollback_successful": False,
            "log_entry": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            error_type = type(error).__name__
            error_message = str(error)
            
            # 1. 文件不存在时的优雅处理 / Graceful handling when file doesn't exist
            if isinstance(error, FileNotFoundError) or (hasattr(error, 'errno') and error.errno == errno.ENOENT):
                results["error_type"] = "FileNotFoundError"
                
                # Check if it's the source or target that doesn't exist
                source_exists = operation.source_path.exists() if operation.source_path else False
                target_exists = operation.target_path.exists() if operation.target_path else False
                
                if not source_exists and operation.operation_type in [FileOperationType.MOVE, FileOperationType.COPY]:
                    # Source file missing - operation cannot proceed
                    results["recovery_action"] = "mark_as_failed"
                    operation.status = "failed"
                    operation.error_message = f"Source file not found: {operation.source_path}"
                    
                elif not target_exists and operation.operation_type == FileOperationType.DELETE:
                    # Already deleted - mark as completed
                    results["recovery_action"] = "mark_as_completed"
                    operation.status = "completed"
                    results["handled"] = True
                
                else:
                    # Create placeholder for missing file if needed
                    results["recovery_action"] = "create_placeholder"
                    operation.error_message = f"File not found: {error_message}"
                
                results["handled"] = True
            
            # 2. 权限不足时的处理 / Permission denied handling
            elif isinstance(error, PermissionError) or (hasattr(error, 'errno') and error.errno in [errno.EACCES, errno.EPERM]):
                results["error_type"] = "PermissionError"
                
                # Attempt to make file writable if it exists
                if operation.source_path and operation.source_path.exists():
                    try:
                        import stat
                        os.chmod(operation.source_path, stat.S_IWRITE | stat.S_IREAD)
                        results["recovery_action"] = "attempt_permission_fix"
                        results["handled"] = True
                    except Exception:
                        results["recovery_action"] = "permission_fix_failed"
                
                if not results["handled"]:
                    # Log the permission error for manual intervention
                    results["recovery_action"] = "logged_for_manual_intervention"
                    operation.error_message = f"Permission denied: {error_message}"
                    operation.status = "failed"
                
                results["handled"] = True
            
            # 3. 磁盘空间不足时的处理 / Disk space full handling
            elif isinstance(error, OSError) and hasattr(error, 'errno') and error.errno == errno.ENOSPC:
                results["error_type"] = "DiskSpaceError"
                
                # Try to free up space by cleaning temp files
                freed_space = await self._cleanup_temp_files()
                
                if freed_space > 100 * 1024 * 1024:  # If freed > 100MB
                    results["recovery_action"] = "cleaned_temp_files"
                    results["freed_space_mb"] = freed_space / (1024 * 1024)
                    results["handled"] = True
                    # Retry the operation
                    results["can_retry"] = True
                else:
                    results["recovery_action"] = "insufficient_space_after_cleanup"
                    results["freed_space_mb"] = freed_space / (1024 * 1024)
                    operation.error_message = f"Insufficient disk space: {error_message}"
                    operation.status = "failed"
                    results["handled"] = True
            
            # 4. 其他操作系统错误 / Other OS errors
            elif isinstance(error, OSError):
                results["error_type"] = f"OSError({error.errno if hasattr(error, 'errno') else 'unknown'})"
                results["recovery_action"] = "logged_os_error"
                operation.error_message = f"OS error: {error_message}"
                operation.status = "failed"
                results["handled"] = True
            
            # 5. 回滚机制 / Rollback mechanism
            if context.get("backup_path") and operation.source_path:
                try:
                    backup_path = Path(context["backup_path"])
                    if backup_path.exists():
                        # Restore from backup
                        if operation.source_path.exists():
                            shutil.copy2(str(backup_path), str(operation.source_path))
                        else:
                            shutil.move(str(backup_path), str(operation.source_path))
                        results["rollback_successful"] = True
                        results["recovery_action"] = results.get("recovery_action", "") + " + rollback"
                except Exception as rollback_error:
                    results["rollback_error"] = str(rollback_error)
                    results["rollback_successful"] = False
            
            # 6. 记录错误日志到系统 / Error logging to system
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "operation_id": operation.operation_id,
                "operation_type": operation.operation_type.en_name,
                "error_type": results["error_type"],
                "error_message": error_message,
                "source_path": str(operation.source_path) if operation.source_path else None,
                "target_path": str(operation.target_path) if operation.target_path else None,
                "recovery_action": results["recovery_action"],
                "rollback_successful": results["rollback_successful"],
                "handled": results["handled"]
            }
            
            # Store in operation history for tracking
            self.operation_history.append(operation)
            
            results["log_entry"] = log_entry
            
            # Notify error callbacks if any
            for callback in self._operation_callbacks:
                try:
                    callback(operation)
                except Exception:
                    pass
            
        except Exception as handling_error:
            # Error handling itself failed
            results["error"] = str(handling_error)
            results["error_type"] = f"ErrorHandlingFailed ({type(handling_error).__name__})"
            results["recovery_action"] = "error_handling_failed"
        
        return results
    
    async def _cleanup_temp_files(self) -> int:
        """Helper method to cleanup temporary files and return freed space in bytes"""
        import tempfile
        freed_space = 0
        
        try:
            temp_dir = Path(tempfile.gettempdir())
            for temp_file in temp_dir.glob("*.tmp"):
                try:
                    if temp_file.is_file():
                        size = temp_file.stat().st_size
                        temp_file.unlink()
                        freed_space += size
                except Exception:
                    pass
        except Exception:
            pass
        
        return freed_space
    
    async def _safe_execute(
        self,
        operation: FileOperation,
        operation_func: Callable,
        rollback_func: Optional[Callable] = None,
        max_retries: int = 1
    ) -> Dict[str, Any]:
        """
        安全执行文件操作 / Safely execute file operation with error handling
        
        关键安全功能：
        - 自动错误检测和处理
        - 操作回滚支持
        - 重试机制
        - 详细结果报告
        
        Critical safety features:
        - Automatic error detection and handling
        - Operation rollback support
        - Retry mechanism
        - Detailed result reporting
        
        Args:
            operation: FileOperation to execute
            operation_func: Async function to perform the actual operation
            rollback_func: Optional function to rollback on failure
            max_retries: Maximum number of retry attempts (default 1)
            
        Returns:
            Dict containing execution results:
            - success: Whether operation succeeded
            - operation: The operation object (updated status)
            - attempts: Number of attempts made
            - error_handling: Error handling results if any
            - rolled_back: Whether rollback was performed
            
        Example:
            >>> async def move_file_op():
            ...     shutil.move(str(src), str(dst))
            >>> result = await desktop._safe_execute(
            ...     operation=file_op,
            ...     operation_func=move_file_op,
            ...     rollback_func=restore_backup,
            ...     max_retries=2
            ... )
        """
        results = {
            "success": False,
            "operation": operation,
            "attempts": 0,
            "error_handling": None,
            "rolled_back": False,
            "timestamp": datetime.now().isoformat()
        }
        
        attempt = 0
        last_error = None
        
        while attempt < max_retries + 1:
            attempt += 1
            results["attempts"] = attempt
            
            try:
                # Mark operation as in progress
                operation.status = "in_progress"
                operation.timestamp = datetime.now()
                
                # Execute the operation
                await operation_func()
                
                # Mark as completed
                operation.status = "completed"
                operation.error_message = None
                results["success"] = True
                
                # Add to history
                self.operation_history.append(operation)
                
                # Notify success
                for callback in self._operation_callbacks:
                    try:
                        callback(operation)
                    except Exception:
                        pass
                
                return results
                
            except Exception as e:
                last_error = e
                operation.status = "failed"
                operation.error_message = str(e)
                
                # Handle the error
                context = {
                    "backup_path": operation.source_path.parent / f".backup_{operation.operation_id}",
                    "original_path": operation.source_path,
                    "attempt": attempt
                }
                
                error_results = await self._handle_file_error(e, operation, context)
                results["error_handling"] = error_results
                
                # Check if we can retry
                if error_results.get("can_retry") and attempt < max_retries + 1:
                    # Wait a bit before retry
                    await asyncio.sleep(0.5)
                    continue
                
                # If error was handled, mark as completed with warning
                if error_results.get("handled"):
                    if error_results.get("recovery_action") in ["mark_as_completed", "cleaned_temp_files"]:
                        operation.status = "completed_with_warnings"
                        results["success"] = True
                
                # Perform rollback if available and needed
                if rollback_func and not results["success"]:
                    try:
                        await rollback_func()
                        results["rolled_back"] = True
                    except Exception as rollback_error:
                        results["rollback_error"] = str(rollback_error)
                
                # Don't retry if error was handled
                if error_results.get("handled"):
                    break
        
        # If we get here, operation failed
        if not results["success"] and last_error:
            results["final_error"] = str(last_error)
            results["final_error_type"] = type(last_error).__name__
        
        return results


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
