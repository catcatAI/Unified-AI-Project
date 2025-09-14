#!/usr/bin/env python3
"""
核心修复引擎 - 统一的修复逻辑管理
"""

import os
import sys
import time
import json
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class FixType(Enum):
    """修复类型枚举"""
    IMPORT_FIX = "import_fix"
    DEPENDENCY_FIX = "dependency_fix"
    SYNTAX_FIX = "syntax_fix"
    CLEANUP_FIX = "cleanup_fix"
    ENVIRONMENT_FIX = "environment_fix"

class FixStatus(Enum):
    """修复状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class FixResult:
    """修复结果类"""
    def __init__(self, fix_type: FixType, target: str):
        self.fix_type = fix_type
        self.target = target
        self.status = FixStatus.PENDING
        self.message = ""
        self.details = {}
        self.start_time = None
        self.end_time = None
        self.error = None
        
    def start(self):
        """开始修复"""
        self.status = FixStatus.IN_PROGRESS
        self.start_time = time.time()
        
    def complete(self, message: str, details: Dict = None):
        """完成修复"""
        self.status = FixStatus.COMPLETED
        self.message = message
        self.details = details or {}
        self.end_time = time.time()
        
    def fail(self, error: str, details: Dict = None):
        """修复失败"""
        self.status = FixStatus.FAILED
        self.error = error
        self.details = details or {}
        self.end_time = time.time()
        
    def skip(self, reason: str):
        """跳过修复"""
        self.status = FixStatus.SKIPPED
        self.message = reason
        self.end_time = time.time()
        
    def get_duration(self) -> Optional[float]:
        """获取修复持续时间"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
        
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "fix_type": self.fix_type.value,
            "target": self.target,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "error": self.error,
            "duration": self.get_duration(),
            "start_time": self.start_time,
            "end_time": self.end_time
        }

class FixEngine:
    """核心修复引擎"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backend_root = project_root / "apps" / "backend"
        self.frontend_root = project_root / "apps" / "frontend-dashboard"
        self.desktop_root = project_root / "apps" / "desktop-app"
        
        self.fix_results: List[FixResult] = []
        self.fix_modules = {}
        self.enabled_fix_types = set()
        
        # 初始化修复模块
        self._initialize_fix_modules()
        
    def _initialize_fix_modules(self):
        """初始化修复模块"""
        try:
            # 导入修复模块
            from scripts.modules.import_fixer import ImportFixer
            from scripts.modules.dependency_fixer import DependencyFixer
            from scripts.modules.syntax_fixer import SyntaxFixer
            from scripts.modules.cleanup_module import CleanupModule
            
            self.fix_modules = {
                FixType.IMPORT_FIX: ImportFixer(self.project_root),
                FixType.DEPENDENCY_FIX: DependencyFixer(self.project_root),
                FixType.SYNTAX_FIX: SyntaxFixer(self.project_root),
                FixType.CLEANUP_FIX: CleanupModule(self.project_root)
            }
            
            # 默认启用所有修复类型
            self.enabled_fix_types = set(self.fix_modules.keys())
            
        except ImportError as e:
            print(f"警告: 无法导入修复模块: {e}")
            self.fix_modules = {}
            
    def enable_fix_type(self, fix_type: FixType):
        """启用修复类型"""
        self.enabled_fix_types.add(fix_type)
        
    def disable_fix_type(self, fix_type: FixType):
        """禁用修复类型"""
        self.enabled_fix_types.discard(fix_type)
        
    def set_enabled_fix_types(self, fix_types: List[FixType]):
        """设置启用的修复类型"""
        self.enabled_fix_types = set(fix_types)
        
    def run_fix(self, fix_type: FixType, target: str = None, **kwargs) -> FixResult:
        """运行特定类型的修复"""
        if fix_type not in self.fix_modules:
            result = FixResult(fix_type, target or "unknown")
            result.fail(f"不支持的修复类型: {fix_type.value}")
            self.fix_results.append(result)
            return result
            
        if fix_type not in self.enabled_fix_types:
            result = FixResult(fix_type, target or "unknown")
            result.skip(f"修复类型已禁用: {fix_type.value}")
            self.fix_results.append(result)
            return result
            
        fix_module = self.fix_modules[fix_type]
        result = FixResult(fix_type, target or "default")
        
        try:
            result.start()
            print(f"开始执行 {fix_type.value} 修复...")
            
            # 调用修复模块的修复方法
            fix_method = getattr(fix_module, 'fix', None)
            if fix_method and callable(fix_method):
                success, message, details = fix_method(target=target, **kwargs)
                
                if success:
                    result.complete(message, details)
                    print(f"✓ {fix_type.value} 修复完成: {message}")
                else:
                    result.fail(message, details)
                    print(f"✗ {fix_type.value} 修复失败: {message}")
            else:
                result.fail("修复模块没有可用的fix方法")
                print(f"✗ {fix_type.value} 修复模块没有可用的fix方法")
                
        except Exception as e:
            error_msg = f"{fix_type.value} 修复时发生异常: {str(e)}"
            result.fail(error_msg, {"traceback": traceback.format_exc()})
            print(f"✗ {error_msg}")
            
        self.fix_results.append(result)
        return result
        
    def run_all_fixes(self, target: str = None, **kwargs) -> Dict[FixType, FixResult]:
        """运行所有启用的修复"""
        results = {}
        
        for fix_type in self.enabled_fix_types:
            results[fix_type] = self.run_fix(fix_type, target, **kwargs)
            
        return results
        
    def run_specific_fixes(self, fix_types: List[FixType], target: str = None, **kwargs) -> Dict[FixType, FixResult]:
        """运行指定的修复类型"""
        results = {}
        
        for fix_type in fix_types:
            results[fix_type] = self.run_fix(fix_type, target, **kwargs)
            
        return results
        
    def get_fix_summary(self) -> Dict:
        """获取修复摘要"""
        summary = {
            "total_fixes": len(self.fix_results),
            "completed": len([r for r in self.fix_results if r.status == FixStatus.COMPLETED]),
            "failed": len([r for r in self.fix_results if r.status == FixStatus.FAILED]),
            "skipped": len([r for r in self.fix_results if r.status == FixStatus.SKIPPED]),
            "in_progress": len([r for r in self.fix_results if r.status == FixStatus.IN_PROGRESS]),
            "by_type": {}
        }
        
        # 按类型统计
        for fix_type in FixType:
            type_results = [r for r in self.fix_results if r.fix_type == fix_type]
            summary["by_type"][fix_type.value] = {
                "total": len(type_results),
                "completed": len([r for r in type_results if r.status == FixStatus.COMPLETED]),
                "failed": len([r for r in type_results if r.status == FixStatus.FAILED]),
                "skipped": len([r for r in type_results if r.status == FixStatus.SKIPPED])
            }
            
        return summary
        
    def get_detailed_results(self) -> List[Dict]:
        """获取详细结果"""
        return [result.to_dict() for result in self.fix_results]
        
    def clear_results(self):
        """清除结果"""
        self.fix_results.clear()
        
    def save_results(self, file_path: Path):
        """保存结果到文件"""
        try:
            results_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "project_root": str(self.project_root),
                "summary": self.get_fix_summary(),
                "detailed_results": self.get_detailed_results()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, ensure_ascii=False, indent=2)
                
            print(f"✓ 修复结果已保存到 {file_path}")
            
        except Exception as e:
            print(f"✗ 保存修复结果时出错: {e}")

def main():
    """测试函数"""
    # 创建修复引擎实例
    engine = FixEngine(PROJECT_ROOT)
    
    # 运行所有修复
    results = engine.run_all_fixes()
    
    # 打印摘要
    summary = engine.get_fix_summary()
    print("修复摘要:")
    print(f"总修复数: {summary['total_fixes']}")
    print(f"完成: {summary['completed']}")
    print(f"失败: {summary['failed']}")
    print(f"跳过: {summary['skipped']}")
    
    # 保存结果
    engine.save_results(PROJECT_ROOT / "fix_engine_test_results.json")

if __name__ == "__main__":
    main()