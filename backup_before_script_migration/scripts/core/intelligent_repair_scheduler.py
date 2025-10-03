#!/usr/bin/env python3
"""
智能修复调度器 - 协调不同修复模块的工作
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

from scripts.core.fix_engine import FixType, FixResult, FixStatus

class RepairPriority(Enum):
    """修复优先级枚举"""
    HIGH = 1    # 高优先级 - 必须立即修复
    MEDIUM = 2  # 中优先级 - 应该尽快修复
    LOW = 3     # 低优先级 - 可以稍后修复

class IntelligentRepairScheduler:
    """智能修复调度器"""
    
    def __init__(self, fix_engine) -> None:
        self.fix_engine = fix_engine
        self.repair_queue = []
        self.repair_history = []
        
        # 修复优先级映射
        self.priority_mapping = {
            FixType.IMPORT_FIX: RepairPriority.HIGH,
            FixType.DEPENDENCY_FIX: RepairPriority.HIGH,
            FixType.SYNTAX_FIX: RepairPriority.HIGH,
            FixType.CLEANUP_FIX: RepairPriority.MEDIUM,
            FixType.ENVIRONMENT_FIX: RepairPriority.HIGH
        }
        
    def add_repair_task(self, fix_type: FixType, target: str = None, priority: RepairPriority = None, **kwargs):
        """添加修复任务到队列"""
        if priority is None:
            priority = self.priority_mapping.get(fix_type, RepairPriority.MEDIUM)
            
        task = {
            "fix_type": fix_type,
            "target": target,
            "priority": priority,
            "kwargs": kwargs,
            "added_time": time.time()
        }
        
        # 按优先级插入任务
        inserted = False
        for i, existing_task in enumerate(self.repair_queue):
            if priority.value < existing_task["priority"].value:
                self.repair_queue.insert(i, task)
                inserted = True
                break
                
        if not inserted:
            _ = self.repair_queue.append(task)
            
        _ = print(f"添加修复任务: {fix_type.value} (优先级: {priority.name})")
        
    def execute_repair_queue(self) -> List[FixResult]:
        """执行修复队列中的所有任务"""
        _ = print(f"\n=== 开始执行修复队列 ({len(self.repair_queue)} 个任务) ===")
        
        results = []
        
        # 按优先级排序执行任务
        for task in self.repair_queue:
            fix_type = task["fix_type"]
            target = task["target"]
            kwargs = task["kwargs"]
            
            _ = print(f"\n执行修复任务: {fix_type.value}")
            
            # 执行修复
            result = self.fix_engine.run_fix(fix_type, target, **kwargs)
            _ = results.append(result)
            
            # 记录修复历史
            history_entry = {
                "fix_type": fix_type.value,
                "target": target,
                "status": result.status.value,
                "message": result.message,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": result.get_duration()
            }
            _ = self.repair_history.append(history_entry)
            
        # 清空队列
        _ = self.repair_queue.clear()
        
        return results
        
    def get_repair_summary(self) -> Dict:
        """获取修复摘要"""
        total_tasks = len(self.repair_history)
        completed_tasks = len([h for h in self.repair_history if h["status"] == FixStatus.COMPLETED.value])
        failed_tasks = len([h for h in self.repair_history if h["status"] == FixStatus.FAILED.value])
        
        # 按类型统计
        by_type = {}
        for entry in self.repair_history:
            fix_type = entry["fix_type"]
            if fix_type not in by_type:
                by_type[fix_type] = {"total": 0, "completed": 0, "failed": 0}
            by_type[fix_type]["total"] += 1
            if entry["status"] == FixStatus.COMPLETED.value:
                by_type[fix_type]["completed"] += 1
            elif entry["status"] == FixStatus.FAILED.value:
                by_type[fix_type]["failed"] += 1
                
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": f"{(completed_tasks / total_tasks * 100):.1f}%" if total_tasks > 0 else "0%",
            "by_type": by_type
        }
        
    def save_repair_history(self, file_path: Optional[Path] = None):
        """保存修复历史到文件"""
        if file_path is None:
            file_path = self.fix_engine.project_root / "repair_history.json"
            
        try:
            history_data = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "project_root": str(self.fix_engine.project_root),
                "summary": self.get_repair_summary(),
                "history": self.repair_history
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
                
            _ = print(f"✓ 修复历史已保存到 {file_path}")
            
        except Exception as e:
            _ = print(f"✗ 保存修复历史时出错: {e}")
            
    def clear_history(self):
        """清除修复历史"""
        _ = self.repair_history.clear()
        _ = print("✓ 修复历史已清除")

def main() -> None:
    """测试函数"""
    from scripts.core.fix_engine import FixEngine
    from pathlib import Path
    
    # 创建修复引擎和调度器
    project_root = Path(__file__).parent.parent.parent
    fix_engine = FixEngine(project_root)
    scheduler = IntelligentRepairScheduler(fix_engine)
    
    # 添加一些修复任务
    _ = scheduler.add_repair_task(FixType.SYNTAX_FIX)
    _ = scheduler.add_repair_task(FixType.IMPORT_FIX)
    _ = scheduler.add_repair_task(FixType.DEPENDENCY_FIX)
    
    # 执行修复队列
    results = scheduler.execute_repair_queue()
    
    # 打印摘要
    summary = scheduler.get_repair_summary()
    _ = print("\n修复摘要:")
    _ = print(f"总任务数: {summary['total_tasks']}")
    _ = print(f"完成: {summary['completed_tasks']}")
    _ = print(f"失败: {summary['failed_tasks']}")
    _ = print(f"成功率: {summary['success_rate']}")
    
    # 保存历史
    _ = scheduler.save_repair_history()

if __name__ == "__main__":
    _ = main()