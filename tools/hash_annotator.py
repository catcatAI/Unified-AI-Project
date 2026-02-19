#!/usr/bin/env python3
# =============================================================================
# FILE_HASH: T001ANNO
# FILE_PATH: tools/hash_annotator.py
# FILE_TYPE: tool
# PURPOSE: 自动为项目文件添加和验证哈希注释
# VERSION: 1.0.0
# STATUS: production_ready
# DEPENDENCIES: hashlib, pathlib, argparse
# LAST_MODIFIED: 2026-02-19
# =============================================================================

"""
Hash Annotator - 哈希注释工具

功能:
1. 为缺失哈希注释的文件自动添加
2. 验证哈希唯一性
3. 更新修改后的文件哈希
4. 生成文件哈希映射数据库

使用方法:
    python tools/hash_annotator.py scan
    python tools/hash_annotator.py annotate --dir apps/backend/src
    python tools/hash_annotator.py validate
    python tools/hash_annotator.py update --file path/to/file.py
"""

import os
import re
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import logging
logger = logging.getLogger(__name__)

# 配置
PROJECT_ROOT = Path(__file__).parent.parent
HASH_DB_PATH = PROJECT_ROOT / ".hashes" / "file_hashes.json"
HASH_LENGTH = 8

# 文件类型映射
FILE_TYPE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".html": "html",
    ".css": "css",
    ".txt": "text",
}

# 注释模板
PYTHON_HEADER_TEMPLATE = """# =============================================================================
# FILE_HASH: {file_hash}
# FILE_PATH: {file_path}
# FILE_TYPE: {file_type}
# PURPOSE: {purpose}
# VERSION: {version}
# STATUS: {status}
# DEPENDENCIES: {dependencies}
# LAST_MODIFIED: {last_modified}
# =============================================================================

"""

JAVASCRIPT_HEADER_TEMPLATE = """/**
 * =============================================================================
 * @file {file_name}
 * @hash {file_hash}
 * @path {file_path}
 * @type {file_type}
 * @purpose {purpose}
 * @version {version}
 * @status {status}
 * @dependencies {dependencies}
 * @lastModified {last_modified}
 * =============================================================================
 */

"""


@dataclass
class FileHashInfo:
    """文件哈希信息"""

    hash: str
    path: str
    type: str
    size: int
    created: str
    modified: str
    has_hash_comment: bool


class HashGenerator:
    """哈希生成器"""

    @staticmethod
    def generate_file_hash(filepath: Path) -> str:
        """生成文件哈希"""
        hash_obj = hashlib.blake2b()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()[:HASH_LENGTH].upper()

    @staticmethod
    def generate_func_hash(func_name: str, file_hash: str) -> str:
        """生成函数哈希"""
        combined = f"{func_name}:{file_hash}"
        return hashlib.blake2b(combined.encode()).hexdigest()[:HASH_LENGTH].upper()


class HashDatabase:
    """哈希数据库管理"""

    def __init__(self, db_path: Path = HASH_DB_PATH):
        self.db_path = db_path
        self.data: Dict[str, dict] = {}
        self.load()

    def load(self):
        """加载数据库"""
        if self.db_path.exists():
            with open(self.db_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    def save(self):
        """保存数据库"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def add(self, file_hash: str, info: dict):
        """添加记录"""
        self.data[file_hash] = info

    def get(self, file_hash: str) -> Optional[dict]:
        """获取记录"""
        return self.data.get(file_hash)

    def find_by_path(self, path: str) -> Optional[dict]:
        """通过路径查找"""
        for hash_id, info in self.data.items():
            if info.get("path") == path:
                return {**info, "hash": hash_id}
        return None

    def check_collision(self, new_hash: str, new_path: str) -> bool:
        """检查哈希碰撞"""
        if new_hash in self.data:
            existing = self.data[new_hash]
            if existing.get("path") != new_path:
                return True
        return False

    def get_all_hashes(self) -> Set[str]:
        """获取所有哈希"""
        return set(self.data.keys())


class FileScanner:
    """文件扫描器"""

    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = project_root
        self.db = HashDatabase()

    def scan_directory(
        self, target_dir: Optional[Path] = None, extensions: Optional[List[str]] = None
    ) -> List[FileHashInfo]:
        """扫描目录"""
        results = []

        if target_dir is None:
            target_dir = self.project_root

        if extensions is None:
            extensions = list(FILE_TYPE_MAP.keys())

        for ext in extensions:
            for filepath in target_dir.rglob(f"*{ext}"):
                if filepath.is_file() and not self._should_ignore(filepath):
                    info = self._analyze_file(filepath)
                    if info:
                        results.append(info)

        return results

    def _should_ignore(self, filepath: Path) -> bool:
        """检查是否应该忽略"""
        ignore_patterns = [
            "__pycache__",
            ".git",
            "node_modules",
            "venv",
            ".venv",
            "archive",
            ".hashes",
        ]

        for pattern in ignore_patterns:
            if pattern in str(filepath):
                return True

        return False

    def _analyze_file(self, filepath: Path) -> Optional[FileHashInfo]:
        """分析文件"""
        try:
            stat = filepath.stat()
            file_hash = HashGenerator.generate_file_hash(filepath)
            rel_path = (
                str(filepath.relative_to(self.project_root)).replace("\\", "/").lower()
            )

            # 检查是否已有哈希注释
            has_hash = self._check_has_hash_comment(filepath)

            return FileHashInfo(
                hash=file_hash,
                path=rel_path,
                type=FILE_TYPE_MAP.get(filepath.suffix, "unknown"),
                size=stat.st_size,
                created=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                has_hash_comment=has_hash,
            )

        except Exception as e:
            print(f"警告: 无法分析 {filepath}: {e}")
            return None

    def _check_has_hash_comment(self, filepath: Path) -> bool:
        """检查文件是否已有哈希注释"""
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(2000)  # 只读前2000字符

            return "FILE_HASH:" in content or "@hash" in content

        except Exception as e:
            logger.error(f'Error in hash_annotator.py: {e}', exc_info=True)
            return False



class HashAnnotator:
    """哈希注释器"""

    def __init__(self, project_root: Path = PROJECT_ROOT):
        self.project_root = project_root
        self.db = HashDatabase()
        self.scanner = FileScanner(project_root)

    def annotate_file(
        self,
        filepath: Path,
        purpose: str = "",
        version: str = "6.2.1",
        status: str = "active",
        dependencies: List[str] = None,
    ) -> bool:
        """为单个文件添加哈希注释"""
        try:
            if dependencies is None:
                dependencies = []

            # 计算哈希
            file_hash = HashGenerator.generate_file_hash(filepath)

            # 检查碰撞
            if self.db.check_collision(file_hash, str(filepath)):
                print(f"错误: 哈希碰撞 detected for {filepath}")
                return False

            # 标准化路径
            rel_path = (
                str(filepath.relative_to(self.project_root)).replace("\\", "/").lower()
            )
            file_type = FILE_TYPE_MAP.get(filepath.suffix, "unknown")

            # 读取原文件
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # 检查是否已有注释
            if "FILE_HASH:" in content[:2000] or "@hash" in content[:2000]:
                print(f"跳过 (已有哈希注释): {filepath}")
                return True

            # 生成注释
            if filepath.suffix == ".py":
                header = PYTHON_HEADER_TEMPLATE.format(
                    file_hash=file_hash,
                    file_path=rel_path,
                    file_type=file_type,
                    purpose=purpose or "Auto-generated",
                    version=version,
                    status=status,
                    dependencies=str(dependencies),
                    last_modified=datetime.now().strftime("%Y-%m-%d"),
                )
            elif filepath.suffix in [".js", ".ts"]:
                header = JAVASCRIPT_HEADER_TEMPLATE.format(
                    file_name=filepath.name,
                    file_hash=file_hash,
                    file_path=rel_path,
                    file_type=file_type,
                    purpose=purpose or "Auto-generated",
                    version=version,
                    status=status,
                    dependencies=str(dependencies),
                    last_modified=datetime.now().strftime("%Y-%m-%d"),
                )
            else:
                print(f"跳过 (不支持的类型): {filepath}")
                return False

            # 写入文件
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(header + content)

            # 更新数据库
            self.db.add(
                file_hash,
                {
                    "path": rel_path,
                    "type": file_type,
                    "purpose": purpose,
                    "version": version,
                    "status": status,
                    "dependencies": dependencies,
                    "annotated_at": datetime.now().isoformat(),
                },
            )
            self.db.save()

            print(f"✓ 已添加注释: {filepath} [{file_hash}]")
            return True

        except Exception as e:
            print(f"✗ 失败: {filepath} - {e}")
            return False

    def annotate_directory(self, target_dir: Path, recursive: bool = True) -> int:
        """为目录添加注释"""
        files = self.scanner.scan_directory(target_dir)

        success_count = 0
        for file_info in files:
            if not file_info.has_hash_comment:
                filepath = self.project_root / file_info.path
                if self.annotate_file(filepath):
                    success_count += 1

        print(f"\n完成: {success_count}/{len(files)} 个文件已添加注释")
        return success_count

    def update_hash(self, filepath: Path) -> Optional[str]:
        """更新文件哈希 (修改后)"""
        try:
            new_hash = HashGenerator.generate_file_hash(filepath)
            rel_path = (
                str(filepath.relative_to(self.project_root)).replace("\\", "/").lower()
            )

            # 查找旧记录
            old_record = self.db.find_by_path(rel_path)
            if old_record:
                old_hash = old_record["hash"]
                # 删除旧记录
                if old_hash in self.db.data:
                    del self.db.data[old_hash]

            # 添加新记录
            self.db.add(
                new_hash, {"path": rel_path, "updated_at": datetime.now().isoformat()}
            )
            self.db.save()

            print(f"✓ 哈希已更新: {filepath} [{new_hash}]")
            return new_hash

        except Exception as e:
            print(f"✗ 更新失败: {filepath} - {e}")
            return None

    def validate_hashes(self) -> Tuple[bool, List[str]]:
        """验证所有哈希"""
        files = self.scanner.scan_directory()
        collisions = []

        all_hashes = self.db.get_all_hashes()

        for file_info in files:
            if self.db.check_collision(file_info.hash, file_info.path):
                collisions.append(f"{file_info.path} [{file_info.hash}]")

            all_hashes.add(file_info.hash)

        if len(all_hashes) != len(files) + len(self.db.data):
            print(f"警告: 发现 {len(collisions)} 个哈希碰撞")
            return False, collisions

        print("✓ 所有哈希验证通过")
        return True, []


def main():
    parser = argparse.ArgumentParser(
        description="哈希注释工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python tools/hash_annotator.py scan
    python tools/hash_annotator.py annotate --dir apps/backend/src
    python tools/hash_annotator.py annotate --file path/to/file.py
    python tools/hash_annotator.py validate
    python tools/hash_annotator.py update --file path/to/file.py
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # scan 命令
    scan_parser = subparsers.add_parser("scan", help="扫描项目文件")
    scan_parser.add_argument("--output", "-o", help="输出JSON文件")

    # annotate 命令
    ann_parser = subparsers.add_parser("annotate", help="添加哈希注释")
    ann_parser.add_argument("--dir", help="目标目录")
    ann_parser.add_argument("--file", help="目标文件")
    ann_parser.add_argument("--purpose", default="Auto-generated", help="文件用途")
    ann_parser.add_argument("--version", default="6.2.1", help="版本号")
    ann_parser.add_argument("--recursive", "-r", action="store_true", help="递归处理")

    # validate 命令
    val_parser = subparsers.add_parser("validate", help="验证哈希")

    # update 命令
    upd_parser = subparsers.add_parser("update", help="更新文件哈希")
    upd_parser.add_argument("--file", required=True, help="目标文件")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    annotator = HashAnnotator()

    if args.command == "scan":
        scanner = FileScanner()
        files = scanner.scan_directory()

        result = {
            "scan_time": datetime.now().isoformat(),
            "total_files": len(files),
            "has_hash": sum(1 for f in files if f.has_hash_comment),
            "missing_hash": sum(1 for f in files if not f.has_hash_comment),
            "files": [asdict(f) for f in files],
        }

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"扫描结果已保存: {args.output}")
        else:
            print(f"总文件数: {result['total_files']}")
            print(f"已有哈希: {result['has_hash']}")
            print(f"缺失哈希: {result['missing_hash']}")

    elif args.command == "annotate":
        if args.file:
            filepath = Path(args.file)
            if not filepath.is_absolute():
                filepath = PROJECT_ROOT / filepath
            annotator.annotate_file(filepath, args.purpose, args.version)
        elif args.dir:
            target_dir = Path(args.dir)
            if not target_dir.is_absolute():
                target_dir = PROJECT_ROOT / target_dir
            annotator.annotate_directory(target_dir, args.recursive)
        else:
            print("错误: 必须指定 --dir 或 --file")

    elif args.command == "validate":
        valid, collisions = annotator.validate_hashes()
        if not valid:
            print("\n碰撞列表:")
            for c in collisions:
                print(f"  - {c}")

    elif args.command == "update":
        filepath = Path(args.file)
        if not filepath.is_absolute():
            filepath = PROJECT_ROOT / filepath
        annotator.update_hash(filepath)


if __name__ == "__main__":
    main()
