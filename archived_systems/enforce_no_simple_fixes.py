#!/usr/bin/env python3
"""
强制执行禁止使用简单修复脚本的监控程序
这个脚本将监控根目录，防止创建新的简单修复脚本
"""

import os
import sys
import time
import hashlib
from pathlib import Path
from datetime import datetime
import json

class SimpleFixScriptEnforcer:
    """简单修复脚本强制执行器"""
    
    def __init__(self):
        self.project_root = Path('.')
        self.baseline_file = self.project_root / '.simple_fix_baseline.json'
        self.forbidden_patterns = [
            'fix.*\\.py$',
            'repair.*\\.py$', 
            'syntax.*\\.py$',
            '.*fixer.*\\.py$',
            '.*repair.*\\.py$'
        ]
        self.allowed_fix_scripts = {
            'unified_auto_fix_system',  # 统一修复系统
            'enforce_no_simple_fixes.py',  # 本监控脚本
            'verify_progress.py',  # 验证脚本
            'quick_verify.py'  # 快速验证脚本
        }
        
    def create_baseline(self):
        """创建当前修复脚本的基线"""
        current_scripts = self._get_current_fix_scripts()
        baseline = {
            'created_at': datetime.now().isoformat(),
            'scripts': current_scripts,
            'count': len(current_scripts),
            'hash': self._calculate_scripts_hash(current_scripts)
        }
        
        with open(self.baseline_file, 'w', encoding='utf-8') as f:
            json.dump(baseline, f, indent=2)
            
        print(f"✅ 基线已创建：{len(current_scripts)}个修复脚本被记录")
        return baseline
        
    def check_violations(self):
        """检查是否有违规创建的修复脚本"""
        if not self.baseline_file.exists():
            print("⚠️  未找到基线文件，创建新基线...")
            self.create_baseline()
            return []
            
        # 加载基线
        with open(self.baseline_file, 'r', encoding='utf-8') as f:
            baseline = json.load(f)
            
        current_scripts = self._get_current_fix_scripts()
        
        # 检查新增脚本
        baseline_scripts = set(baseline['scripts'].keys())
        current_scripts_set = set(current_scripts.keys())
        new_scripts = current_scripts_set - baseline_scripts
        
        violations = []
        for script in new_scripts:
            if script not in self.allowed_fix_scripts:
                violations.append({
                    'script': script,
                    'type': 'new_simple_fix_script',
                    'message': f'检测到新的简单修复脚本: {script}'
                })
                
        return violations
        
    def _get_current_fix_scripts(self):
        """获取当前所有的修复脚本"""
        fix_scripts = {}
        
        for py_file in self.project_root.glob('*.py'):
            filename = py_file.name
            
            # 检查是否匹配禁止模式
            if self._is_fix_script(filename):
                # 检查文件内容
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                
                script_info = {
                    'path': str(py_file),
                    'size': py_file.stat().st_size,
                    'modified': datetime.fromtimestamp(py_file.stat().st_mtime).isoformat(),
                    'content_hash': hashlib.md5(content.encode()).hexdigest()[:8],
                    'has_fix_functions': self._has_fix_functions(content),
                    'complexity_score': self._calculate_complexity(content)
                }
                
                fix_scripts[filename] = script_info
                
        return fix_scripts
        
    def _is_fix_script(self, filename):
        """判断是否为修复脚本"""
        import re
        
        # 检查禁止模式
        for pattern in self.forbidden_patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                return True
                
        # 检查文件内容是否包含修复相关关键词
        return False  # 不过度分析内容，主要基于文件名
        
    def _has_fix_functions(self, content):
        """检查是否包含修复函数"""
        fix_keywords = [
            'def fix_', 'def repair_', 'def correct_',
            'syntax_fix', 'import_fix', 'indent_fix',
            'replace(', 're.sub', 'regex'
        ]
        
        content_lower = content.lower()
        return sum(1 for keyword in fix_keywords if keyword in content_lower)
        
    def _calculate_complexity(self, content):
        """计算脚本复杂度（简单估算）"""
        lines = content.split('\n')
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        
        # 基于代码行数和函数数量估算
        function_count = content.count('def ')
        class_count = content.count('class ')
        
        return {
            'total_lines': len(lines),
            'code_lines': len(code_lines),
            'functions': function_count,
            'classes': class_count
        }
        
    def _calculate_scripts_hash(self, scripts_dict):
        """计算脚本集合的哈希值"""
        content = json.dumps(scripts_dict, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()[:16]
        
    def generate_report(self):
        """生成监控报告"""
        print("🔒 简单修复脚本强制执行监控报告")
        print("=" * 60)
        print(f"检查时间: {datetime.now()}")
        print()
        
        # 检查违规
        violations = self.check_violations()
        
        if violations:
            print("🚨 发现违规！")
            print()
            for violation in violations:
                print(f"❌ {violation['message']}")
                print(f"   类型: {violation['type']}")
                print()
                
            print("⚡ 立即行动要求:")
            print("1. 删除所有违规创建的简单修复脚本")
            print("2. 使用统一自动修复系统进行修复")
            print("3. 重新创建基线记录")
            return False
        else:
            print("✅ 未发现违规创建简单修复脚本")
            print("✅ 项目符合统一修复系统使用规范")
            return True
            
    def monitor_continuously(self, interval=300):  # 5分钟检查一次
        """持续监控模式"""
        print(f"🔍 开始持续监控模式（每{interval}秒检查一次）")
        print("按 Ctrl+C 停止监控")
        
        try:
            while True:
                self.generate_report()
                print(f"\n⏰ 下次检查: {datetime.now().timestamp() + interval}")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n✅ 监控已停止")
            
    def cleanup_simple_scripts(self):
        """清理现有的简单修复脚本（谨慎使用）"""
        print("🧹 开始清理简单修复脚本...")
        
        current_scripts = self._get_current_fix_scripts()
        cleaned_count = 0
        
        for script_name, script_info in current_scripts.items():
            if script_name in self.allowed_fix_scripts:
                continue
                
            # 检查脚本的复杂度
            complexity = script_info.get('complexity_score', {})
            
            # 如果脚本过于简单（少于50行代码，少于2个函数），建议清理
            if (complexity.get('code_lines', 0) < 50 and 
                complexity.get('functions', 0) < 2 and
                script_info.get('has_fix_functions', 0) > 0):
                
                script_path = Path(script_info['path'])
                backup_path = script_path.with_suffix('.py.backup')
                
                print(f"⚠️  发现简单修复脚本: {script_name}")
                print(f"   代码行数: {complexity.get('code_lines', 0)}")
                print(f"   函数数量: {complexity.get('functions', 0)}")
                
                # 移动到备份目录而不是直接删除
                script_path.rename(backup_path)
                print(f"   ✅ 已备份到: {backup_path}")
                cleaned_count += 1
                
        print(f"\n🎯 清理完成: {cleaned_count}个简单脚本被备份")
        print("📁 备份文件保存在原位置，扩展名为.backup")
        
        return cleaned_count


def main():
    """主函数"""
    enforcer = SimpleFixScriptEnforcer()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'create-baseline':
            enforcer.create_baseline()
            
        elif command == 'check':
            enforcer.generate_report()
            
        elif command == 'monitor':
            enforcer.monitor_continuously()
            
        elif command == 'cleanup':
            confirm = input("⚠️  这将备份现有的简单修复脚本，是否继续？(y/N): ")
            if confirm.lower() == 'y':
                enforcer.cleanup_simple_scripts()
                enforcer.create_baseline()  # 重新创建基线
                
        elif command == 'help':
            print("使用方法:")
            print("  python enforce_no_simple_fixes.py create-baseline  # 创建基线")
            print("  python enforce_no_simple_fixes.py check            # 检查违规")
            print("  python enforce_no_simple_fixes.py monitor          # 持续监控")
            print("  python enforce_no_simple_fixes.py cleanup          # 清理简单脚本")
            print("  python enforce_no_simple_fixes.py help             # 显示帮助")
            
        else:
            print(f"未知命令: {command}")
            print("使用 'help' 查看可用命令")
    else:
        # 默认执行检查
        enforcer.generate_report()


if __name__ == "__main__":
    main()
