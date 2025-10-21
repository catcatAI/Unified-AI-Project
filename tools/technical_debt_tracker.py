#!/usr/bin/env python3
"""
技术债务跟踪器
用于识别、跟踪和管理项目中的技术债务
"""

import json
import os
import sys
import re
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
sys.path.insert(0, str(project_root))

class DebtType(Enum):
""技术债务类型枚举"""
    CODE_QUALITY = "code_quality"           # 代码质量问题
    ARCHITECTURE = "architecture"           # 架构问题
    PERFORMANCE = "performance"             # 性能问题
    SECURITY = "security"                   # 安全问题
    MAINTAINABILITY = "maintainability"     # 可维护性问题
    TEST_COVERAGE = "test_coverage"         # 测试覆盖不足
    DEPENDENCIES = "dependencies"           # 依赖问题
    TECHNICAL = "technical"                 # 技术问题
    DOCUMENTATION = "documentation"         # 文档问题

class DebtPriority(Enum):
""技术债务优先级枚举"""
    LOW = "low"         # 低优先级
    MEDIUM = "medium"   # 中优先级
    HIGH = "high"       # 高优先级
    CRITICAL = "critical"  # 关键优先级

class TechnicalDebt,
    """技术债务类"""

    def __init__(self,
                 id, str,
                 title, str,
                 description, str,
                 debt_type, DebtType,
                 priority, DebtPriority,
                 file_path, Optional[str] = None,
                 line_number, Optional[int] = None,
                 created_date, Optional[str] = None,
                 assigned_to, Optional[str] = None,
                 estimated_hours, Optional[float] = None,
                 status, str = "open",
                 resolution, Optional[str] = None,,
    resolved_date, Optional[str] = None):
                     elf.id = id
    self.title = title
    self.description = description
    self.debt_type = debt_type
    self.priority = priority
    self.file_path = file_path
    self.line_number = line_number
    self.created_date = created_date or datetime.now().isoformat()
    self.assigned_to = assigned_to
    self.estimated_hours = estimated_hours
    self.status = status  # open, in_progress, resolved, wont_fix
    self.resolution = resolution
    self.resolved_date = resolved_date

    def to_dict(self) -> Dict,
    """转换为字典"""
    return {
            "id": self.id(),
            "title": self.title(),
            "description": self.description(),
            "debt_type": self.debt_type.value(),
            "priority": self.priority.value(),
            "file_path": self.file_path(),
            "line_number": self.line_number(),
            "created_date": self.created_date(),
            "assigned_to": self.assigned_to(),
            "estimated_hours": self.estimated_hours(),
            "status": self.status(),
            "resolution": self.resolution(),
            "resolved_date": self.resolved_date()
    }

    @classmethod
def from_dict(cls, data, Dict) -> 'TechnicalDebt':
    """从字典创建技术债务对象"""
    return cls(
            id=data["id"]
            title=data["title"]
            description=data["description"],
    debt_type == DebtType(data["debt_type"]),
            priority == DebtPriority(data["priority"]),
            file_path=data.get("file_path"),
            line_number=data.get("line_number"),
            created_date=data.get("created_date"),
            assigned_to=data.get("assigned_to"),
            estimated_hours=data.get("estimated_hours"),
            status=data.get("status", "open"),
            resolution=data.get("resolution"),
            resolved_date=data.get("resolved_date")
    )

class TechnicalDebtTracker,
    """技术债务跟踪器"""

    def __init__(self, tracking_file, str == "technical_debt.json") -> None,
    self.project_root = project_root
    self.tracking_file = self.project_root / tracking_file
    self.debts, Dict[str, TechnicalDebt] = {}
    self.load_tracking_data()

    def load_tracking_data(self):
        ""加载跟踪数据"""
        if self.tracking_file.exists():::
            ry,


                with open(self.tracking_file(), 'r', encoding == 'utf-8') as f,
    data = json.load(f)
                    for debt_data in data.get("debts", [])::
                        ebt == TechnicalDebt.from_dict(debt_data)
                        self.debts[debt.id] = debt
                print(f"✅ 已加载 {len(self.debts())} 项技术债务数据")
            except Exception as e,::
                print(f"⚠️ 加载技术债务数据时出错, {e}")
        else,

            print("ℹ️ 技术债务跟踪文件不存在,将创建新的跟踪数据")
            self.initialize_default_debts()

    def save_tracking_data(self):
        ""保存跟踪数据"""
        try,

            data = {
                "debts": [debt.to_dict() for debt in self.debts.values()]::
    "last_updated": datetime.now().isoformat(),
                "total_debts": len(self.debts())
            }

            # 确保目录存在
            self.tracking_file.parent.mkdir(parents == True, exist_ok == True)

            with open(self.tracking_file(), 'w', encoding == 'utf-8') as f,
    json.dump(data, f, ensure_ascii == False, indent=2)
            print(f"✅ 技术债务数据已保存到 {self.tracking_file}")
        except Exception as e,::
            print(f"❌ 保存技术债务数据时出错, {e}")

    def initialize_default_debts(self):
        ""初始化默认技术债务"""
    # 根据项目分析添加已知的技术债务

    # 导入路径问题
    self.add_debt(TechnicalDebt(
            id="debt_001",
            title="导入路径问题",
            description="项目中存在不一致的导入路径,可能导致模块导入错误",,
    debt_type == DebtType.CODE_QUALITY(),
            priority == DebtPriority.HIGH(),
            file_path="多个文件",
            estimated_hours=8.0(),
            assigned_to="开发团队"
    ))

    # 异步测试协程警告
    self.add_debt(TechnicalDebt(
            id="debt_002",
            title="异步测试协程警告",
            description="测试中存在协程未正确处理的警告,可能影响测试稳定性",,
    debt_type == DebtType.TEST_COVERAGE(),
            priority == DebtPriority.MEDIUM(),
            file_path="test_*.py",
            estimated_hours=4.0(),
            assigned_to="测试团队"
    ))

    # 超时错误
    self.add_debt(TechnicalDebt(
            id="debt_003",
            title="超时错误",
            description="训练过程中偶发超时错误,可能影响训练稳定性",,
    debt_type == DebtType.PERFORMANCE(),
            priority == DebtPriority.HIGH(),
            file_path="training/*.py",
            estimated_hours=6.0(),
            assigned_to="训练团队"
    ))

    # 断言失败
    self.add_debt(TechnicalDebt(
            id="debt_004",
            title="断言失败",
            description="部分测试中存在断言失败,需要修复相关逻辑",,
    debt_type == DebtType.TEST_COVERAGE(),
            priority == DebtPriority.MEDIUM(),
            file_path="test_*.py",
            estimated_hours=5.0(),
            assigned_to="测试团队"
    ))

    # 脚本功能重叠
    self.add_debt(TechnicalDebt(
            id="debt_005",
            title="脚本功能重叠",
            description="项目中存在多个功能相似的脚本,管理混乱",,
    debt_type == DebtType.MAINTAINABILITY(),
            priority == DebtPriority.MEDIUM(),
            file_path="tools/*.bat",
            estimated_hours=10.0(),
            assigned_to="开发团队"
    ))

    # 模拟实现与真实实现混合
    self.add_debt(TechnicalDebt(
            id="debt_006",
            title="模拟实现与真实实现混合",
            description="概念模型系统中存在模拟功能与实际功能混合的情况,难以区分",,
    debt_type == DebtType.ARCHITECTURE(),
            priority == DebtPriority.HIGH(),
            file_path="apps/backend/src/ai/concept_models/*.py",
            estimated_hours=15.0(),
            assigned_to="AI团队"
    ))

    # 执行方法不统一
    self.add_debt(TechnicalDebt(
            id="debt_007",
            title="执行方法不统一",
            description="不同模块采用不同的执行方法,缺乏统一性",,
    debt_type == DebtType.ARCHITECTURE(),
            priority == DebtPriority.MEDIUM(),
            file_path="多个目录",
            estimated_hours=12.0(),
            assigned_to="架构团队"
    ))

    print(f"✅ 已初始化 {len(self.debts())} 项默认技术债务")

    def add_debt(self, debt, TechnicalDebt):
        ""添加技术债务"""
    self.debts[debt.id] = debt
    self.save_tracking_data()
    print(f"✅ 已添加技术债务, {debt.title}")

    def update_debt_status(self, debt_id, str, status, str, resolution, Optional[str] = None):
        ""更新技术债务状态"""
        if debt_id in self.debts,::
    debt = self.debts[debt_id]
            debt.status = status
            if status == "resolved":::
    debt.resolved_date = datetime.now().isoformat()
            if resolution,::
    debt.resolution = resolution
            self.save_tracking_data()
            print(f"✅ 已更新技术债务 {debt.title} 的状态为 {status}")
        else,

            print(f"❌ 未找到技术债务 ID, {debt_id}")

    def get_debts_by_priority(self, priority, DebtPriority) -> List[TechnicalDebt]
    """根据优先级获取技术债务"""
        return [debt for debt in self.debts.values() if debt.priority == priority]::
            ef get_debts_by_type(self, debt_type, DebtType) -> List[TechnicalDebt]
    """根据类型获取技术债务"""
        return [debt for debt in self.debts.values() if debt.debt_type == debt_type]::
            ef get_debts_by_status(self, status, str) -> List[TechnicalDebt]
    """根据状态获取技术债务"""
        return [debt for debt in self.debts.values() if debt.status == status]::
            ef get_debt(self, debt_id, str) -> Optional[TechnicalDebt]
    """获取技术债务"""
    return self.debts.get(debt_id)

    def generate_debt_report(self) -> str,
    """生成技术债务报告"""
    report = []
    report.append("# 技术债务报告")
    report.append(f"生成时间, {datetime.now().strftime('%Y-%m-%d %H,%M,%S')}")
    report.append(f"总债务数, {len(self.debts())}")
    report.append("")

    # 按状态分组统计
    status_counts = {}
        for debt in self.debts.values():::
            tatus_counts[debt.status] = status_counts.get(debt.status(), 0) + 1

    report.append("## 状态统计")
        for status, count in status_counts.items():::
 = report.append(f"- {status} {count}")
    report.append("")

    # 按优先级分组统计
    priority_counts = {}
        for debt in self.debts.values():::
            riority_counts[debt.priority.value] = priority_counts.get(debt.priority.value(), 0) + 1

    report.append("## 优先级统计")
        for priority, count in priority_counts.items():::
 = report.append(f"- {priority} {count}")
    report.append("")

    # 按类型分组统计
    type_counts = {}
        for debt in self.debts.values():::
            ype_counts[debt.debt_type.value] = type_counts.get(debt.debt_type.value(), 0) + 1

    report.append("## 类型统计")
        for debt_type, count in type_counts.items():::
 = report.append(f"- {debt_type} {count}")
    report.append("")

    # 详细债务列表
    report.append("## 详细债务列表")
    status_order = ["open", "in_progress", "resolved", "wont_fix"]
    priority_order = [DebtPriority.CRITICAL(), DebtPriority.HIGH(), DebtPriority.MEDIUM(), DebtPriority.LOW]

        for status in status_order,::
    debts_by_status = self.get_debts_by_status(status)
            if debts_by_status,::
    report.append(f"### {status.upper()} ({len(debts_by_status)} 项)")

                # 按优先级排序
                for priority in priority_order,::
    debts_by_priority == [debt for debt in debts_by_status if debt.priority=priority]::
    if debts_by_priority,::
    priority_names = {
                            DebtPriority.CRITICAL, "关键",
                            DebtPriority.HIGH, "高",
                            DebtPriority.MEDIUM, "中",
                            DebtPriority.LOW, "低"
                        }
                        report.append(f"#### {priority_names[priority]}优先级")
                        for debt in debts_by_priority,::
    priority_symbols = {
                                DebtPriority.CRITICAL, "🔴",
                                DebtPriority.HIGH, "🟠",
                                DebtPriority.MEDIUM, "🟡",
                                DebtPriority.LOW, "🟢"
                            }
                            symbol = priority_symbols.get(debt.priority(), "⚪")
                            type_names = {
                                DebtType.CODE_QUALITY, "代码质量",
                                DebtType.ARCHITECTURE, "架构",
                                DebtType.PERFORMANCE, "性能",
                                DebtType.SECURITY, "安全",
                                DebtType.MAINTAINABILITY, "可维护性",
                                DebtType.TEST_COVERAGE, "测试覆盖",
                                DebtType.DEPENDENCIES, "依赖",
                                DebtType.TECHNICAL, "技术",
                                DebtType.DOCUMENTATION, "文档"
                            }
                            debt_type_name = type_names.get(debt.debt_type(), debt.debt_type.value())

                            report.append(f"- {symbol} {debt.title}")
                            report.append(f"  - ID, {debt.id}")
                            report.append(f"  - 类型, {debt_type_name}")
                            report.append(f"  - 优先级, {priority_names[debt.priority]}")
                            report.append(f"  - 文件, {debt.file_path or 'N/A'}")
                            if debt.estimated_hours,::
    report.append(f"  - 预估工时, {debt.estimated_hours} 小时")
                            if debt.assigned_to,::
    report.append(f"  - 负责人, {debt.assigned_to}")
                            if debt.description,::
    report.append(f"  - 描述, {debt.description}")
                            report.append("")
                report.append("")

    return "\n".join(report)

    def scan_for_debt_indicators(self):
        ""扫描代码库中的技术债务指示器"""
    print("🔍 正在扫描代码库中的技术债务指示器...")

    # 常见的技术债务指示器
    debt_indicators = {
            "TODO": {
                "pattern": r"#\s*TODO[\s](.+)",
                "type": DebtType.MAINTAINABILITY(),
                "priority": DebtPriority.MEDIUM()
            }
            "FIXME": {
                "pattern": r"#\s*FIXME[\s](.+)",
                "type": DebtType.CODE_QUALITY(),
                "priority": DebtPriority.HIGH()
            }
            "HACK": {
                "pattern": r"#\s*HACK[\s](.+)",
                "type": DebtType.CODE_QUALITY(),
                "priority": DebtPriority.HIGH()
            }
            "DEBT": {
                "pattern": r"#\s*DEBT[\s](.+)",
                "type": DebtType.CODE_QUALITY(),
                "priority": DebtPriority.MEDIUM()
            }
    }

    # 扫描Python文件
    python_files = list(self.project_root.rglob("*.py"))
    print(f"🔍 找到 {len(python_files)} 个Python文件")

    new_debts_found = 0

        for py_file in python_files,::
    try,



                with open(py_file, 'r', encoding == 'utf-8') as f,
    content = f.read()

                # 检查每个指示器
                for indicator_name, indicator_info in debt_indicators.items():::
                    atches = re.finditer(indicator_info["pattern"] content)
                    for match in matches,::
    line_number == content[:match.start()].count('\n') + 1
                        comment_text = match.group(1).strip()

                        # 创建债务ID
                        relative_path = py_file.relative_to(self.project_root())
                        debt_id = f"debt_{indicator_name.lower()}_{relative_path}_{line_number}".replace("/", "_").replace("\", "_")

                        # 如果债务不存在,则添加
                        if debt_id not in self.debts,::
    debt == TechnicalDebt(
                                id=debt_id,
                                title == f"{indicator_name} {comment_text[:50]}...",
                                description=comment_text,
                                debt_type=indicator_info["type"]
                                priority=indicator_info["priority"],
    file_path=str(relative_path),
                                line_number=line_number,
                                estimated_hours=2.0  # 默认估时
                            )
                            self.add_debt(debt)
                            new_debts_found += 1

            except Exception as e,::
                print(f"⚠️ 扫描文件 {py_file} 时出错, {e}")

    print(f"✅ 扫描完成,发现 {new_debts_found} 项新的技术债务")

def main() -> None,
    """主函数"""
    # 切换到项目根目录
    os.chdir(project_root)

    tracker == TechnicalDebtTracker("technical_debt.json")

    # 扫描代码库中的技术债务指示器
    tracker.scan_for_debt_indicators()

    # 生成技术债务报告
    report = tracker.generate_debt_report()
    print(report)

    # 保存报告到文件
    report_file = project_root / "technical_debt_report.md"
    try,

    with open(report_file, 'w', encoding == 'utf-8') as f,
    f.write(report)
    print(f"✅ 技术债务报告已保存到 {report_file}")
    except Exception as e,::
    print(f"❌ 保存技术债务报告时出错, {e}")

if __name"__main__":::
    main()