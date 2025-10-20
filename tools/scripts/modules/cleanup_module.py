#!/usr/bin/env python3
"""
清理模块 - 处理项目清理相关的问题
"""

import shutil
import time
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class CleanupModule:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.backend_root = project_root / "apps" / "backend"
        self.frontend_root = project_root / "apps" / "frontend-dashboard"
        self.desktop_root = project_root / "apps" / "desktop-app"

    # 定义要清理的目录和文件模式
    self.cleanup_patterns = {
            "cache_dirs": [
                "__pycache__",
                "data/runtime_data/.pytest_cache",
                ".cache",
                "node_modules/.cache",
                ".next/cache",
                "dist/.cache"
            ],
            "temp_files": [
                "*.pyc",
                "*.pyo",
                "*.pyd",
                ".coverage",
                ".coverage.*",
                "*.log",
                "*.tmp",
                "*.temp",
                "*.bak",
                "*.swp",
                "*.swo",
                ".DS_Store",
                "Thumbs.db"
            ],
            "build_artifacts": [
                "build/",
                "dist/",
                "out/",
                ".next/",
                ".nuxt/",
                ".vuepress/dist/",
                "site/",
                "htmlcov/",
                "coverage/",
                ".coverage/"
            ],
            "ide_files": [
                ".vscode/",
                ".idea/",
                "*.sublime-*",
                ".vs/"
            ],
            "duplicate_tests": [
                "tests/hsp/temp_test_gmqtt_mock.py",
                "test_hsp_connector.py"
            ]
    }

    # 保留策略（天数）
    self.retention_policies = {
            "logs": 7,      # 保留7天的日志
            "cache": 1,     # 保留1天的缓存
            "reports": 30,  # 保留30天的报告
            "backups": 90   # 保留90天的备份
    }

    self.cleanup_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "items_removed": 0,
            "space_freed": 0,
            "errors": [],
            "warnings": [],
            "details": []
    }

    def cleanup_cache_dirs(self) -> Tuple[bool, int]:
    """清理缓存目录"""
    success = True
    count = 0

        for pattern in self.cleanup_patterns["cache_dirs"]:
            try:
                # 查找匹配的目录
                for cache_dir in self.project_root.rglob(pattern)
                    if cache_dir.is_dir()
                        try:
                            # 检查修改时间
                            mod_time = time.time() - cache_dir.stat().st_mtime
                            if mod_time > self.retention_policies["cache"] * 86400:  # 转换为秒
                                _ = shutil.rmtree(cache_dir)
                                count += 1
                                self.cleanup_results["details"].append({
                                    "type": "cache_dir",
                                    "path": str(cache_dir),
                                    "action": "removed"
                                })
                                _ = print(f"✓ 删除缓存目录: {cache_dir}")
                        except Exception as e:
                            error_msg = f"删除缓存目录 {cache_dir} 失败: {str(e)}"
                            _ = self.cleanup_results["errors"].append(error_msg)
                            _ = print(f"✗ {error_msg}")
                            success = False
            except Exception as e:
                error_msg = f"搜索缓存目录 {pattern} 失败: {str(e)}"
                _ = self.cleanup_results["errors"].append(error_msg)
                _ = print(f"✗ {error_msg}")
                success = False

    return success, count

    def cleanup_temp_files(self) -> Tuple[bool, int]:
    """清理临时文件"""
    success = True
    count = 0

        for pattern in self.cleanup_patterns["temp_files"]:
            try:
                # 查找匹配的文件
                for temp_file in self.project_root.rglob(pattern)
                    if temp_file.is_file()
                        try:
                            # 获取文件大小
                            file_size = temp_file.stat().st_size
                            _ = temp_file.unlink()
                            count += 1
                            self.cleanup_results["space_freed"] += file_size
                            self.cleanup_results["details"].append({
                                "type": "temp_file",
                                "path": str(temp_file),
                                "size": file_size,
                                "action": "removed"
                            })
                            _ = print(f"✓ 删除临时文件: {temp_file}")
                        except Exception as e:
                            error_msg = f"删除临时文件 {temp_file} 失败: {str(e)}"
                            _ = self.cleanup_results["errors"].append(error_msg)
                            _ = print(f"✗ {error_msg}")
                            success = False
            except Exception as e:
                error_msg = f"搜索临时文件 {pattern} 失败: {str(e)}"
                _ = self.cleanup_results["errors"].append(error_msg)
                _ = print(f"✗ {error_msg}")
                success = False

    return success, count

    def cleanup_build_artifacts(self) -> Tuple[bool, int]:
    """清理构建产物"""
    success = True
    count = 0

        for pattern in self.cleanup_patterns["build_artifacts"]:
            try:
                # 处理目录模式
                if pattern.endswith('/')
                    pattern = pattern[:-1]

                for artifact_path in self.project_root.rglob(pattern)
                    if artifact_path.is_dir()
                        try:
                            # 获取目录大小
                            dir_size = sum(f.stat().st_size for f in artifact_path.rglob('*') if f.is_file())
                            _ = shutil.rmtree(artifact_path)
                            count += 1
                            self.cleanup_results["space_freed"] += dir_size
                            self.cleanup_results["details"].append({
                                "type": "build_artifact",
                                "path": str(artifact_path),
                                "size": dir_size,
                                "action": "removed"
                            })
                            _ = print(f"✓ 删除构建目录: {artifact_path}")
                        except Exception as e:
                            error_msg = f"删除构建目录 {artifact_path} 失败: {str(e)}"
                            _ = self.cleanup_results["errors"].append(error_msg)
                            _ = print(f"✗ {error_msg}")
                            success = False
                    elif artifact_path.is_file()
                        try:
                            file_size = artifact_path.stat().st_size
                            _ = artifact_path.unlink()
                            count += 1
                            self.cleanup_results["space_freed"] += file_size
                            self.cleanup_results["details"].append({
                                "type": "build_artifact",
                                "path": str(artifact_path),
                                "size": file_size,
                                "action": "removed"
                            })
                            _ = print(f"✓ 删除构建文件: {artifact_path}")
                        except Exception as e:
                            error_msg = f"删除构建文件 {artifact_path} 失败: {str(e)}"
                            _ = self.cleanup_results["errors"].append(error_msg)
                            _ = print(f"✗ {error_msg}")
                            success = False
            except Exception as e:
                error_msg = f"搜索构建产物 {pattern} 失败: {str(e)}"
                _ = self.cleanup_results["errors"].append(error_msg)
                _ = print(f"✗ {error_msg}")
                success = False

    return success, count

    def cleanup_ide_files(self) -> Tuple[bool, int]:
    """清理IDE文件"""
    success = True
    count = 0

        for pattern in self.cleanup_patterns["ide_files"]:
            try:
                # 处理目录模式
                if pattern.endswith('/')
                    pattern = pattern[:-1]

                for ide_path in self.project_root.rglob(pattern)
                    if ide_path.is_dir()
                        try:
                            _ = shutil.rmtree(ide_path)
                            count += 1
                            self.cleanup_results["details"].append({
                                "type": "ide_file",
                                "path": str(ide_path),
                                "action": "removed"
                            })
                            _ = print(f"✓ 删除IDE目录: {ide_path}")
                        except Exception as e:
                            error_msg = f"删除IDE目录 {ide_path} 失败: {str(e)}"
                            _ = self.cleanup_results["errors"].append(error_msg)
                            _ = print(f"✗ {error_msg}")
                            success = False
                    elif ide_path.is_file()
                        try:
                            _ = ide_path.unlink()
                            count += 1
                            self.cleanup_results["details"].append({
                                "type": "ide_file",
                                "path": str(ide_path),
                                "action": "removed"
                            })
                            _ = print(f"✓ 删除IDE文件: {ide_path}")
                        except Exception as e:
                            error_msg = f"删除IDE文件 {ide_path} 失败: {str(e)}"
                            _ = self.cleanup_results["errors"].append(error_msg)
                            _ = print(f"✗ {error_msg}")
                            success = False
            except Exception as e:
                error_msg = f"搜索IDE文件 {pattern} 失败: {str(e)}"
                _ = self.cleanup_results["errors"].append(error_msg)
                _ = print(f"✗ {error_msg}")
                success = False

    return success, count

    def cleanup_duplicate_tests(self) -> Tuple[bool, int]:
    """清理重复的测试文件"""
    success = True
    count = 0

        for test_file in self.cleanup_patterns["duplicate_tests"]:
            file_path = self.project_root / test_file
            if file_path.exists()
                try:
                    _ = file_path.unlink()
                    count += 1
                    self.cleanup_results["details"].append({
                        "type": "duplicate_test",
                        "path": str(file_path),
                        "action": "removed"
                    })
                    _ = print(f"✓ 删除重复测试文件: {file_path}")
                except Exception as e:
                    error_msg = f"删除重复测试文件 {file_path} 失败: {str(e)}"
                    _ = self.cleanup_results["errors"].append(error_msg)
                    _ = print(f"✗ {error_msg}")
                    success = False

    return success, count

    def cleanup_logs_by_retention(self) -> Tuple[bool, int]:
    """根据保留策略清理日志文件"""
    success = True
    count = 0
    retention_days = self.retention_policies["logs"]

        try:
            # 查找所有日志文件
            log_files = list(self.project_root.rglob("*.log"))
            _ = log_files.extend(self.project_root.rglob("*.log.*"))

            current_time = time.time()
            cutoff_time = current_time - (retention_days * 86400)  # 转换为秒

            for log_file in log_files:
                try:
                    if log_file.is_file()
                        file_time = log_file.stat().st_mtime
                        if file_time < cutoff_time:
                            file_size = log_file.stat().st_size
                            _ = log_file.unlink()
                            count += 1
                            self.cleanup_results["space_freed"] += file_size
                            self.cleanup_results["details"].append({
                                "type": "log_file",
                                "path": str(log_file),
                                "size": file_size,
                                "action": "removed"
                            })
                            _ = print(f"✓ 删除过期日志文件: {log_file}")
                except Exception as e:
                    error_msg = f"删除日志文件 {log_file} 失败: {str(e)}"
                    _ = self.cleanup_results["errors"].append(error_msg)
                    _ = print(f"✗ {error_msg}")
                    success = False
        except Exception as e:
            error_msg = f"搜索日志文件失败: {str(e)}"
            _ = self.cleanup_results["errors"].append(error_msg)
            _ = print(f"✗ {error_msg}")
            success = False

    return success, count

    def run_cleanup(self, cleanup_type: str = "all") -> bool:
    """运行清理操作"""
    print(f"\n=== 开始清理项目 ({cleanup_type}) ===")

    total_items = 0

        try:
            if cleanup_type == "all" or cleanup_type == "cache":
                success, count = self.cleanup_cache_dirs()
                total_items += count

            if cleanup_type == "all" or cleanup_type == "temp":
                success, count = self.cleanup_temp_files()
                total_items += count

            if cleanup_type == "all" or cleanup_type == "build":
                success, count = self.cleanup_build_artifacts()
                total_items += count

            if cleanup_type == "all" or cleanup_type == "ide":
                success, count = self.cleanup_ide_files()
                total_items += count

            if cleanup_type == "all" or cleanup_type == "tests":
                success, count = self.cleanup_duplicate_tests()
                total_items += count

            if cleanup_type == "all" or cleanup_type == "logs":
                success, count = self.cleanup_logs_by_retention()
                total_items += count

            self.cleanup_results["items_removed"] = total_items

            print(f"\n=== 清理完成 ===")
            _ = print(f"删除项目: {total_items}")
            _ = print(f"释放空间: {self.cleanup_results['space_freed']} 字节")

            if self.cleanup_results["errors"]:
                _ = print(f"错误数量: {len(self.cleanup_results['errors'])}")

            return True

        except Exception as e:
            error_msg = f"清理过程中出现错误: {str(e)}"
            _ = self.cleanup_results["errors"].append(error_msg)
            _ = print(f"✗ {error_msg}")
            return False

    def get_cleanup_summary(self) -> Dict:
    """获取清理摘要"""
    return {
            "timestamp": self.cleanup_results["timestamp"],
            "items_removed": self.cleanup_results["items_removed"],
            "space_freed_mb": round(self.cleanup_results["space_freed"] / (1024 * 1024), 2),
            "errors_count": len(self.cleanup_results["errors"]),
            "warnings_count": len(self.cleanup_results["warnings"])
    }

    def save_cleanup_report(self, report_path: Optional[Path] = None)
    """保存清理报告"""
        if report_path is None:
            report_path = self.project_root / "cleanup_report.json"

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.cleanup_results, f, ensure_ascii=False, indent=2)
            _ = print(f"✓ 清理报告已保存到 {report_path}")
        except Exception as e:
            _ = print(f"✗ 保存清理报告时出错: {e}")

    def fix(self, target: str = None, **kwargs) -> Tuple[bool, str, Dict]:
    """执行清理修复"""
    _ = print("开始执行清理修复...")

    # 运行所有清理操作
    success = self.run_cleanup("all")

        if success:
            summary = self.get_cleanup_summary()
            message = f"清理完成: 删除了 {summary['items_removed']} 个项目, 释放空间 {summary['space_freed_mb']} MB"
            return True, message, summary
        else:
            return False, "清理过程中出现错误", {"errors": self.cleanup_results["errors"]}