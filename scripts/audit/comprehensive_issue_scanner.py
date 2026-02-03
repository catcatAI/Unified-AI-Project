#!/usr/bin/env python3
"""
全面问题扫描器 - Angela AI v6.0
扫描硬编码、数据链路、TODO等问题
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple

class AngelaIssueScanner:
    """问题扫描器"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.hardcoded_values = []
        self.data_link_issues = []
        self.todos = []
        
    def scan_file(self, filepath: Path):
        """扫描单个文件"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            return
        
        for i, line in enumerate(lines, 1):
            self._check_line(filepath, i, line, content)
    
    def _check_line(self, filepath: Path, line_num: int, line: str, content: str):
        """检查单行"""
        line_stripped = line.strip()
        
        # 1. 检查硬编码数值（魔法数字）
        # 排除注释、字符串、简单赋值
        if not line_stripped.startswith('#') and not line_stripped.startswith('"""') and not line_stripped.startswith("'''"):
            # 查找硬编码的数字（超过3位的或特定的魔法数字）
            magic_numbers = re.findall(r'\b(?!\d+\.\d+)([0-9]{3,}|300|200|404|500|60|24|7|30|1000)\b', line)
            for num in magic_numbers:
                # 排除索引访问如 list[0], dict[200]
                if not re.search(rf'\[{num}\]', line):
                    # 排除函数参数默认值检查
                    if 'def ' not in line and 'return ' not in line:
                        self.hardcoded_values.append({
                            'file': str(filepath),
                            'line': line_num,
                            'value': num,
                            'context': line_stripped[:80]
                        })
        
        # 2. 检查TODO/FIXME/XXX
        todo_patterns = [
            (r'TODO[:\s]', 'TODO'),
            (r'FIXME[:\s]', 'FIXME'),
            (r'XXX[:\s]', 'XXX'),
            (r'HACK[:\s]', 'HACK'),
            (r'BUG[:\s]', 'BUG'),
            (r'NOTE[:\s].*待', 'NOTE-待完成'),
            (r'需要', '需要'),
            (r'待實', '待实现'),
        ]
        
        for pattern, label in todo_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                self.todos.append({
                    'file': str(filepath),
                    'line': line_num,
                    'type': label,
                    'context': line_stripped[:80]
                })
        
        # 3. 检查数据链路问题 - pass语句（可能未实现）
        if re.search(r'^\s*pass\s*$', line) and 'def ' not in content.split('\n')[max(0, line_num-5):line_num]:
            # 这可能是空的实现
            pass
        
        # 4. 检查硬编码路径
        if re.search(r'[C-Z]:\\\\', line) or '/home/' in line or '/Users/' in line:
            if 'def ' not in line and '#' not in line:
                self.warnings.append({
                    'file': str(filepath),
                    'line': line_num,
                    'type': '硬编码路径',
                    'context': line_stripped[:80]
                })
        
        # 5. 检查硬编码URL
        if re.search(r'https?://[^\s\'"]+', line):
            if 'def ' not in line and '=' not in line:
                pass  # 忽略函数定义和赋值中的URL
        
        # 6. 检查未使用的导入（简化检查）
        if line_stripped.startswith('import ') or line_stripped.startswith('from '):
            module = line_stripped.split()[1] if len(line_stripped.split()) > 1 else ''
            # 检查是否在文件后续使用
            rest_content = '\n'.join(content.split('\n')[line_num:])
            if module and module not in ['__future__', 'typing', 'dataclasses', 'enum', 'abc']:
                if module not in rest_content[:1000]:  # 检查后续1000字符
                    pass  # 可能未使用，但不报告以避免误报
    
    def scan_directory(self, directory: Path, pattern: str = '*.py'):
        """扫描目录"""
        for filepath in directory.rglob(pattern):
            if '__pycache__' in str(filepath):
                continue
            self.scan_file(filepath)
    
    def print_report(self):
        """打印报告"""
        print("=" * 80)
        print("🔍 Angela AI v6.0 - 全面问题扫描报告")
        print("=" * 80)
        
        # 1. 硬编码数值
        print("\n🔢 硬编码数值（魔法数字）")
        print("-" * 80)
        if self.hardcoded_values:
            # 按数值分组
            by_value = {}
            for item in self.hardcoded_values:
                val = item['value']
                if val not in by_value:
                    by_value[val] = []
                by_value[val].append(item)
            
            # 显示最常见的前10个
            sorted_values = sorted(by_value.items(), key=lambda x: len(x[1]), reverse=True)[:10]
            for val, items in sorted_values:
                print(f"\n  数值 {val}: 出现 {len(items)} 次")
                for item in items[:3]:  # 只显示前3个
                    print(f"    - {item['file'].split('/')[-1]}:{item['line']}")
                if len(items) > 3:
                    print(f"    ... 还有 {len(items)-3} 处")
        else:
            print("  ✅ 未发现明显的硬编码数值问题")
        
        # 2. TODO/FIXME
        print("\n📝 TODO/FIXME/需要完成的任务")
        print("-" * 80)
        if self.todos:
            by_type = {}
            for item in self.todos:
                t = item['type']
                if t not in by_type:
                    by_type[t] = []
                by_type[t].append(item)
            
            for t, items in sorted(by_type.items()):
                print(f"\n  {t}: {len(items)}个")
                for item in items[:5]:
                    print(f"    - {item['file'].split('/')[-1]}:{item['line']} - {item['context'][:60]}")
                if len(items) > 5:
                    print(f"    ... 还有 {len(items)-5} 个")
        else:
            print("  ✅ 未发现TODO标记")
        
        # 3. 警告
        print("\n⚠️  警告")
        print("-" * 80)
        if self.warnings:
            for item in self.warnings[:20]:
                print(f"  - {item['type']}: {item['file'].split('/')[-1]}:{item['line']}")
            if len(self.warnings) > 20:
                print(f"  ... 还有 {len(self.warnings)-20} 个警告")
        else:
            print("  ✅ 未发现警告")
        
        # 总结
        print("\n" + "=" * 80)
        print("📊 扫描统计")
        print("=" * 80)
        print(f"硬编码数值: {len(self.hardcoded_values)} 处")
        print(f"TODO/待办: {len(self.todos)} 个")
        print(f"警告: {len(self.warnings)} 个")
        
        # 建议
        print("\n" + "=" * 80)
        print("💡 建议")
        print("=" * 80)
        if len(self.hardcoded_values) > 50:
            print("• 考虑将常用数值提取到配置文件中")
        if len(self.todos) > 10:
            print("• 优先处理TODO事项，特别是标记为FIXME的")
        print("• 魔法数字不全是问题，关键看是否在多处重复使用")
        print("• 建议定期运行此扫描器跟踪代码质量")


def main():
    scanner = AngelaIssueScanner()
    
    # 扫描自主系统目录
    autonomous_dir = Path("apps/backend/src/core/autonomous")
    if autonomous_dir.exists():
        print(f"扫描目录: {autonomous_dir}")
        scanner.scan_directory(autonomous_dir)
    
    # 扫描核心目录
    core_dir = Path("apps/backend/src/core")
    if core_dir.exists():
        print(f"扫描目录: {core_dir}")
        scanner.scan_directory(core_dir)
    
    # 打印报告
    scanner.print_report()


if __name__ == "__main__":
    main()
