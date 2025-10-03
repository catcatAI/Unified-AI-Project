#!/usr/bin/env python3
"""
Unified AI Project 重构计划更新脚本
此脚本用于根据执行过程中发现的问题更新重构计划
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any

class PlanUpdater:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.progress_file = self.project_root / "refactor_progress.json"
        self.plan_file = self.project_root / "PROJECT_REFACTOR_PLAN.md"
        self.checklist_file = self.project_root / "REFATOR_CHECKLIST.md"
        self.progress_report_file = self.project_root / "REFACTOR_PROGRESS_REPORT.md"
        self.summary_report_file = self.project_root / "REFACTOR_SUMMARY_REPORT.md"
        
        # 加载进度
        self.progress = self.load_progress()
    
    def load_progress(self) -> Dict[str, Any]:
        """加载重构进度"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "current_phase": 0,
                "completed_tasks": [],
                "issues_found": [],
                "plan_updates": []
            }
    
    def update_plan_files(self):
        """根据发现的问题更新计划文件"""
        print("开始更新重构计划文件...")
        
        # 1. 更新PROJECT_REFACTOR_PLAN.md
        self.update_main_plan()
        
        # 2. 更新REFATOR_CHECKLIST.md
        self.update_checklist()
        
        # 3. 更新REFACTOR_PROGRESS_REPORT.md
        self.update_progress_report()
        
        # 4. 更新REFACTOR_SUMMARY_REPORT.md
        self.update_summary_report()
        
        print("重构计划文件更新完成")
    
    def update_main_plan(self):
        """更新主计划文件"""
        if not self.plan_file.exists():
            print("主计划文件不存在，跳过更新")
            return
        
        # 读取现有计划文件
        with open(self.plan_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加发现的问题和更新
        updates_made = False
        
        # 检查是否需要添加HAM记忆系统对比任务
        if any("HAM记忆系统" in issue["issue"] for issue in self.progress["issues_found"]):
            if "### 4.10 第十阶段：HAM记忆系统对比分析" not in content:
                # 在实施步骤部分添加新阶段
                new_phase = """
### 4.10 第十阶段：HAM记忆系统对比分析 (2天)
1. 详细对比主实现和备份实现的HAM记忆系统
2. 识别备份实现中的有用功能
3. 合并有用功能到主实现
4. 验证合并后功能完整性

### 4.11 第十一阶段：BaseAgent系统对比分析 (2天)
1. 详细对比两个版本的BaseAgent实现
2. 识别功能差异和优劣
3. 合并有用功能到主实现
4. 验证合并后功能完整性
"""
                content = content.replace("## 5. 风险评估和缓解措施", new_phase + "\n## 5. 风险评估和缓解措施")
                updates_made = True
        
        # 检查是否需要更新时间估算
        if updates_made:
            # 更新时间估算表
            time_table = """
| 阶段 | 任务 | 预估时间 |
|------|------|----------|
| 第一阶段 | 备份和准备工作 | 1天 |
| 第二阶段 | 文件夹结构重组 | 2天 |
| 第三阶段 | 重复文件处理 | 2天 |
| 第四阶段 | 零散文件处理 | 2天 |
| 第五阶段 | 新旧功能整合 | 3天 |
| 第六阶段 | 测试优化 | 3天 |
| 第七阶段 | 导入路径更新 | 3天 |
| 第八阶段 | 服务初始化优化 | 2天 |
| 第九阶段 | 测试和验证 | 2天 |
| 第十阶段 | HAM记忆系统对比分析 | 2天 |
| 第十一阶段 | BaseAgent系统对比分析 | 2天 |
| **总计** |  | **22天** |
"""
            # 替换旧的时间估算表
            import re
            content = re.sub(
                r"\| 阶段 \| 任务 \| 预估时间 \|(.*?)\| \*\*总计\*\* \|  \| \*\*20天\*\* \|",
                time_table,
                content,
                flags=re.DOTALL
            )
        
        # 保存更新后的内容
        if updates_made:
            with open(self.plan_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("主计划文件已更新")
        else:
            print("主计划文件无需更新")
    
    def update_checklist(self):
        """更新检查清单文件"""
        if not self.checklist_file.exists():
            print("检查清单文件不存在，跳过更新")
            return
        
        # 读取现有检查清单文件
        with open(self.checklist_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加新的检查项
        updates_made = False
        
        # 检查是否需要添加HAM记忆系统对比检查项
        if any("HAM记忆系统" in issue["issue"] for issue in self.progress["issues_found"]):
            if "### 10.1 HAM记忆系统对比分析" not in content:
                new_checklist = """
### 10.1 HAM记忆系统对比分析
- [ ] 对比主实现和备份实现的HAM记忆系统
- [ ] 识别备份实现中的有用功能
- [ ] 制定功能合并计划
- [ ] 验证合并后功能完整性

### 10.2 BaseAgent系统对比分析
- [ ] 对比两个版本的BaseAgent实现
- [ ] 识别功能差异和优劣
- [ ] 制定功能合并计划
- [ ] 验证合并后功能完整性
"""
                content = content.replace("## 10. 后续维护检查项", new_checklist + "\n## 10. 后续维护检查项")
                updates_made = True
        
        # 保存更新后的内容
        if updates_made:
            with open(self.checklist_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("检查清单文件已更新")
        else:
            print("检查清单文件无需更新")
    
    def update_progress_report(self):
        """更新进度报告文件"""
        if not self.progress_report_file.exists():
            print("进度报告文件不存在，跳过更新")
            return
        
        # 读取现有进度报告文件
        with open(self.progress_report_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加新的阶段
        updates_made = False
        
        # 检查是否需要添加新的阶段
        if any("HAM记忆系统" in issue["issue"] for issue in self.progress["issues_found"]):
            if "### 4.10 第十阶段：HAM记忆系统对比分析" not in content:
                new_phases = """
### 4.10 第十阶段：HAM记忆系统对比分析 (2天)
- [ ] 详细对比主实现和备份实现的HAM记忆系统
- [ ] 识别备份实现中的有用功能
- [ ] 合并有用功能到主实现
- [ ] 验证合并后功能完整性

### 4.11 第十一阶段：BaseAgent系统对比分析 (2天)
- [ ] 详细对比两个版本的BaseAgent实现
- [ ] 识别功能差异和优劣
- [ ] 合并有用功能到主实现
- [ ] 验证合并后功能完整性
"""
                content = content.replace("## 5. 风险和问题", new_phases + "\n## 5. 风险和问题")
                updates_made = True
        
        # 更新资源需求
        if updates_made:
            # 更新时间估算
            content = content.replace("预计总时间：20个工作日", "预计总时间：22个工作日")
        
        # 保存更新后的内容
        if updates_made:
            with open(self.progress_report_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("进度报告文件已更新")
        else:
            print("进度报告文件无需更新")
    
    def update_summary_report(self):
        """更新总结报告文件"""
        if not self.summary_report_file.exists():
            print("总结报告文件不存在，跳过更新")
            return
        
        # 读取现有总结报告文件
        with open(self.summary_report_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加新的实施过程
        updates_made = False
        
        # 检查是否需要添加新的实施过程
        if any("HAM记忆系统" in issue["issue"] for issue in self.progress["issues_found"]):
            if "### 4.10 第十阶段：HAM记忆系统对比分析" not in content:
                new_phases = """
### 4.10 第十阶段：HAM记忆系统对比分析
- 详细对比主实现和备份实现的HAM记忆系统
- 识别备份实现中的有用功能
- 合并有用功能到主实现
- 验证合并后功能完整性

### 4.11 第十一阶段：BaseAgent系统对比分析
- 详细对比两个版本的BaseAgent实现
- 识别功能差异和优劣
- 合并有用功能到主实现
- 验证合并后功能完整性
"""
                content = content.replace("## 5. 成果总结", new_phases + "\n## 5. 成果总结")
                updates_made = True
        
        # 更新时间估算
        if updates_made:
            content = content.replace("预计总时间：20个工作日", "预计总时间：22个工作日")
        
        # 保存更新后的内容
        if updates_made:
            with open(self.summary_report_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("总结报告文件已更新")
        else:
            print("总结报告文件无需更新")
    
    def generate_action_plan(self):
        """生成具体行动计划"""
        print("生成具体行动计划...")
        
        action_plan = []
        
        # 根据发现的问题生成具体行动
        for issue in self.progress["issues_found"]:
            if "HAM记忆系统" in issue["issue"]:
                action_plan.append({
                    "task": "对比HAM记忆系统主实现和备份实现",
                    "description": "详细对比apps/backend/src/ai/memory/ham_memory_manager.py和backup_modules/ai_backup/memory/ham_memory_manager.py的差异",
                    "priority": "high",
                    "estimated_time": "2天"
                })
            elif "BaseAgent" in issue["issue"]:
                action_plan.append({
                    "task": "对比BaseAgent主实现和备份实现",
                    "description": "详细对比apps/backend/src/agents/base_agent.py和apps/backend/src/ai/agents/base/base_agent.py的差异",
                    "priority": "high",
                    "estimated_time": "2天"
                })
            elif "backup_modules目录" in issue["issue"]:
                action_plan.append({
                    "task": "删除backup_modules目录",
                    "description": "删除backup_modules目录下的重复文件",
                    "priority": "medium",
                    "estimated_time": "1天"
                })
            elif "迁移文档文件" in issue["issue"]:
                action_plan.append({
                    "task": "迁移文档文件到docs目录",
                    "description": "将根目录下的153个MD文件迁移到docs目录的相应子目录",
                    "priority": "medium",
                    "estimated_time": "2天"
                })
            elif "迁移脚本文件" in issue["issue"]:
                action_plan.append({
                    "task": "迁移脚本文件到tools/scripts目录",
                    "description": "将scripts目录下的文件迁移到tools/scripts目录",
                    "priority": "medium",
                    "estimated_time": "1天"
                })
            elif "合并功能相似的文件" in issue["issue"]:
                action_plan.append({
                    "task": "分析和合并功能相似的文件",
                    "description": "详细分析并合并功能相似的文件",
                    "priority": "medium",
                    "estimated_time": "3天"
                })
            elif "运行测试验证功能完整性" in issue["issue"]:
                action_plan.append({
                    "task": "运行测试验证功能完整性",
                    "description": "运行所有测试来验证功能完整性",
                    "priority": "high",
                    "estimated_time": "2天"
                })
            elif "对比主实现和备份实现的差异" in issue["issue"]:
                action_plan.append({
                    "task": "详细对比实现差异",
                    "description": "详细对比主实现和备份实现的差异",
                    "priority": "high",
                    "estimated_time": "3天"
                })
        
        # 保存行动计划
        action_plan_file = self.project_root / "ACTION_PLAN.md"
        with open(action_plan_file, 'w', encoding='utf-8') as f:
            f.write("# Unified AI Project 重构行动计划\n\n")
            for i, action in enumerate(action_plan, 1):
                f.write(f"## {i}. {action['task']}\n")
                f.write(f"**描述**: {action['description']}\n")
                f.write(f"**优先级**: {action['priority']}\n")
                f.write(f"**预估时间**: {action['estimated_time']}\n\n")
        
        print(f"行动计划已生成: {action_plan_file}")
        return action_plan
    
    def run(self):
        """运行计划更新器"""
        print("开始更新重构计划...")
        
        try:
            # 更新计划文件
            self.update_plan_files()
            
            # 生成具体行动计划
            action_plan = self.generate_action_plan()
            
            print("重构计划更新完成")
            print(f"生成了 {len(action_plan)} 个具体行动任务")
            
        except Exception as e:
            print(f"更新过程中发生错误: {e}")
            raise

def main():
    """主函数"""
    # 获取项目根目录
    project_root = os.getcwd()
    
    # 创建并运行计划更新器
    updater = PlanUpdater(project_root)
    updater.run()

if __name__ == "__main__":
    main()