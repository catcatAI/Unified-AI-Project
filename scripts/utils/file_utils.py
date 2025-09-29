#!/usr/bin/env python3
"""
文件工具模块 - 提供文件操作相关的通用功能
"""

import shutil
import hashlib
import fnmatch
import time
from pathlib import Path
class FileType(Enum):
    """文件类型枚举"""
    PYTHON = "python"              # Python文件
    JAVASCRIPT = "javascript"      # JavaScript文件
    TYPESCRIPT = "typescript"      # TypeScript文件
    JSON = "json"                  # JSON文件
    YAML = "yaml"                  # YAML文件
    MARKDOWN = "markdown"          # Markdown文件
    TEXT = "text"                  # 文本文件
    BINARY = "binary"              # 二进制文件
    UNKNOWN = "unknown"            # 未知类型

class FileOperation(Enum):
    """文件操作枚举"""
    COPY = "copy"                  # 复制
    MOVE = "move"                  # 移动
    DELETE = "delete"              # 删除
    RENAME = "rename"              # 重命名
    CREATE = "create"              # 创建
    MODIFY = "modify"              # 修改

class FileUtils:
    """文件工具类"""
    
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        
        # 文件类型映射
        self.file_type_mappings = {
            ".py": FileType.PYTHON,
            ".js": FileType.JAVASCRIPT,
            ".ts": FileType.TYPESCRIPT,
            ".json": FileType.JSON,
            ".yaml": FileType.YAML,
            ".yml": FileType.YAML,
            ".md": FileType.MARKDOWN,
            ".txt": FileType.TEXT,
            ".log": FileType.TEXT,
            ".csv": FileType.TEXT,
            ".xml": FileType.TEXT,
            ".html": FileType.TEXT,
            ".css": FileType.TEXT,
            ".scss": FileType.TEXT,
            ".less": FileType.TEXT,
            ".sql": FileType.TEXT,
            ".sh": FileType.TEXT,
            ".bat": FileType.TEXT,
            ".ps1": FileType.TEXT,
            ".ini": FileType.TEXT,
            ".toml": FileType.TEXT,
            ".cfg": FileType.TEXT,
            ".conf": FileType.TEXT,
        }
        
        # 需要排除的目录和文件
        self.exclude_patterns = [
            "__pycache__",
            ".pytest_cache",
            ".git",
            ".vscode",
            ".idea",
            "node_modules",
            "venv",
            ".venv",
            "env",
            "dist",
            "build",
            "out",
            ".next",
            ".nuxt",
            "coverage",
            ".coverage",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".DS_Store",
            "Thumbs.db"
        ]
    
    def get_file_type(self, file_path: Path) -> FileType:
        """获取文件类型"""
        suffix = file_path.suffix.lower()
        return self.file_type_mappings.get(suffix, FileType.UNKNOWN)
    
    def is_text_file(self, file_path: Path) -> bool:
        """判断是否为文本文件"""
        file_type = self.get_file_type(file_path)
        return file_type in [FileType.PYTHON, FileType.JAVASCRIPT, FileType.TYPESCRIPT,
                           FileType.JSON, FileType.YAML, FileType.MARKDOWN, FileType.TEXT]
    
    def is_binary_file(self, file_path: Path) -> bool:
        """判断是否为二进制文件"""
        return not self.is_text_file(file_path)
    
    def read_file(self, file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
        """读取文件内容"""
        try:
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            _ = print(f"✗ 读取文件 {file_path} 失败: {e}")
            return None
    
    def write_file(self, file_path: Path, content: str, encoding: str = 'utf-8',
                   create_dirs: bool = True) -> bool:
        """写入文件内容"""
        try:
            if create_dirs:
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                _ = f.write(content)
            
            return True
        except Exception as e:
            _ = print(f"✗ 写入文件 {file_path} 失败: {e}")
            return False
    
    def append_file(self, file_path: Path, content: str, encoding: str = 'utf-8') -> bool:
        """追加文件内容"""
        try:
            with open(file_path, 'a', encoding=encoding) as f:
                _ = f.write(content)
            
            return True
        except Exception as e:
            _ = print(f"✗ 追加文件 {file_path} 失败: {e}")
            return False
    
    def copy_file(self, src_path: Path, dst_path: Path, 
                  create_dirs: bool = True) -> bool:
        """复制文件"""
        try:
            if create_dirs:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            _ = shutil.copy2(src_path, dst_path)
            return True
        except Exception as e:
            _ = print(f"✗ 复制文件 {src_path} 到 {dst_path} 失败: {e}")
            return False
    
    def move_file(self, src_path: Path, dst_path: Path, 
                  create_dirs: bool = True) -> bool:
        """移动文件"""
        try:
            if create_dirs:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            _ = shutil.move(str(src_path), str(dst_path))
            return True
        except Exception as e:
            _ = print(f"✗ 移动文件 {src_path} 到 {dst_path} 失败: {e}")
            return False
    
    def delete_file(self, file_path: Path) -> bool:
        """删除文件"""
        try:
            if file_path.exists():
                _ = file_path.unlink()
            return True
        except Exception as e:
            _ = print(f"✗ 删除文件 {file_path} 失败: {e}")
            return False
    
    def create_directory(self, dir_path: Path, parents: bool = True) -> bool:
        """创建目录"""
        try:
            dir_path.mkdir(parents=parents, exist_ok=True)
            return True
        except Exception as e:
            _ = print(f"✗ 创建目录 {dir_path} 失败: {e}")
            return False
    
    def delete_directory(self, dir_path: Path) -> bool:
        """删除目录"""
        try:
            if dir_path.exists():
                _ = shutil.rmtree(dir_path)
            return True
        except Exception as e:
            _ = print(f"✗ 删除目录 {dir_path} 失败: {e}")
            return False
    
    def find_files(self, root_path: Path, pattern: str = "*", 
                   recursive: bool = True, exclude_patterns: Optional[List[str]] = None) -> List[Path]:
        """查找文件"""
        if exclude_patterns is None:
            exclude_patterns = self.exclude_patterns
        
        files = []
        
        if recursive:
            for file_path in root_path.rglob(pattern):
                if not self._is_excluded(file_path, exclude_patterns):
                    _ = files.append(file_path)
        else:
            for file_path in root_path.glob(pattern):
                if not self._is_excluded(file_path, exclude_patterns):
                    _ = files.append(file_path)
        
        return sorted(files)
    
    def find_files_by_type(self, root_path: Path, file_type: FileType, 
                          recursive: bool = True) -> List[Path]:
        """按类型查找文件"""
        extensions = [ext for ext, ft in self.file_type_mappings.items() if ft == file_type]
        
        files = []
        for ext in extensions:
            pattern = f"*{ext}"
            _ = files.extend(self.find_files(root_path, pattern, recursive))
        
        return files
    
    def find_files_by_content(self, root_path: Path, search_text: str, 
                             file_types: Optional[List[FileType]] = None,
                             case_sensitive: bool = False) -> List[Path]:
        """按内容查找文件"""
        if file_types is None:
            file_types = [FileType.PYTHON, FileType.JAVASCRIPT, FileType.TYPESCRIPT,
                         FileType.JSON, FileType.YAML, FileType.MARKDOWN, FileType.TEXT]
        
        matching_files = []
        
        for file_type in file_types:
            files = self.find_files_by_type(root_path, file_type)
            
            for file_path in files:
                content = self.read_file(file_path)
                if content:
                    if case_sensitive:
                        if search_text in content:
                            _ = matching_files.append(file_path)
                    else:
                        if search_text.lower() in content.lower():
                            _ = matching_files.append(file_path)
        
        return matching_files
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            if not file_path.exists():
                return {}
            
            stat = file_path.stat()
            
            return {
                _ = "path": str(file_path),
                "name": file_path.name,
                "size": stat.st_size,
                _ = "size_mb": round(stat.st_size / (1024 * 1024), 2),
                _ = "type": self.get_file_type(file_path).value,
                _ = "is_text": self.is_text_file(file_path),
                _ = "is_binary": self.is_binary_file(file_path),
                _ = "created": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_ctime)),
                _ = "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                _ = "accessed": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_atime)),
                _ = "permissions": oct(stat.st_mode)[-3:]
            }
        except Exception as e:
            _ = print(f"✗ 获取文件信息 {file_path} 失败: {e}")
            return {}
    
    def get_directory_info(self, dir_path: Path) -> Dict[str, Any]:
        """获取目录信息"""
        try:
            if not dir_path.exists():
                return {}
            
            files = self.find_files(dir_path, recursive=False)
            directories = [d for d in dir_path.iterdir() if d.is_dir()]
            
            total_size = sum(f.stat().st_size for f in files if f.exists())
            
            file_types = {}
            for file_path in files:
                file_type = self.get_file_type(file_path)
                file_types[file_type.value] = file_types.get(file_type.value, 0) + 1
            
            return {
                _ = "path": str(dir_path),
                "name": dir_path.name,
                _ = "files_count": len(files),
                _ = "directories_count": len(directories),
                "total_size": total_size,
                _ = "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "created": time.strftime("%Y-%m-%d %H:%M:%S", 
                                       _ = time.localtime(dir_path.stat().st_ctime)),
                "modified": time.strftime("%Y-%m-%d %H:%M:%S", 
                                       _ = time.localtime(dir_path.stat().st_mtime))
            }
        except Exception as e:
            _ = print(f"✗ 获取目录信息 {dir_path} 失败: {e}")
            return {}
    
    def calculate_file_hash(self, file_path: Path, algorithm: str = "md5") -> Optional[str]:
        """计算文件哈希值"""
        try:
            if not file_path.exists():
                return None
            
            hash_func = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    _ = hash_func.update(chunk)
            
            return hash_func.hexdigest()
        except Exception as e:
            _ = print(f"✗ 计算文件哈希 {file_path} 失败: {e}")
            return None
    
    def compare_files(self, file1: Path, file2: Path) -> Dict[str, Any]:
        """比较两个文件"""
        try:
            if not file1.exists() or not file2.exists():
                return {"error": "文件不存在"}
            
            info1 = self.get_file_info(file1)
            info2 = self.get_file_info(file2)
            
            # 比较大小
            size_equal = info1.get("size") == info2.get("size")
            
            # 比较内容
            content_equal = False
            if size_equal:
                hash1 = self.calculate_file_hash(file1)
                hash2 = self.calculate_file_hash(file2)
                content_equal = hash1 == hash2
            
            return {
                "file1": info1,
                "file2": info2,
                "size_equal": size_equal,
                "content_equal": content_equal,
                "identical": size_equal and content_equal
            }
        except Exception as e:
            _ = print(f"✗ 比较文件 {file1} 和 {file2} 失败: {e}")
            return {"error": str(e)}
    
    def backup_file(self, file_path: Path, backup_dir: Optional[Path] = None) -> Optional[Path]:
        """备份文件"""
        try:
            if not file_path.exists():
                return None
            
            if backup_dir is None:
                backup_dir = file_path.parent / "backups"
            
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成备份文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name
            
            # 复制文件
            _ = shutil.copy2(file_path, backup_path)
            
            return backup_path
        except Exception as e:
            _ = print(f"✗ 备份文件 {file_path} 失败: {e}")
            return None
    
    def restore_file(self, backup_path: Path, target_path: Optional[Path] = None) -> bool:
        """恢复文件"""
        try:
            if not backup_path.exists():
                return False
            
            if target_path is None:
                # 从备份文件名中提取原始文件名
                name_parts = backup_path.stem.split('_')
                if len(name_parts) >= 2:
                    original_name = '_'.join(name_parts[:-1]) + backup_path.suffix
                    target_path = backup_path.parent.parent / original_name
                else:
                    return False
            
            # 复制备份文件
            _ = shutil.copy2(backup_path, target_path)
            
            return True
        except Exception as e:
            _ = print(f"✗ 恢复文件 {backup_path} 失败: {e}")
            return False
    
    def _is_excluded(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """判断文件是否被排除"""
        # 检查文件路径中的每个部分
        for part in file_path.parts:
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(part, pattern):
                    return True
        
        # 检查文件名
        for pattern in exclude_patterns:
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
        
        return False
    
    def clean_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        import re
        
        # 替换非法字符为下划线
        cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # 移除控制字符
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
        
        # 确保文件名不为空
        if not cleaned:
            cleaned = "unnamed"
        
        return cleaned
    
    def get_relative_path(self, file_path: Path, base_path: Path) -> Path:
        """获取相对路径"""
        try:
            return file_path.relative_to(base_path)
        except ValueError:
            # 如果文件不在基础路径下，返回绝对路径
            return file_path
    
    def ensure_unique_filename(self, file_path: Path) -> Path:
        """确保文件名唯一"""
        if not file_path.exists():
            return file_path
        
        counter = 1
        while True:
            new_name = f"{file_path.stem}_{counter}{file_path.suffix}"
            new_path = file_path.parent / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1