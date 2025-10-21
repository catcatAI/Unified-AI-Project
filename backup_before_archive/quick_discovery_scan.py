#!/usr/bin/env python3
"""
快速问题发现扫描
运行现有的检测工具并汇总结果
"""

import subprocess
import sys
import os
from pathlib import Path

def run_quick_discovery():
    """运行快速问题发现"""
    print("🔍 启动快速问题发现扫描...")
    print("="*60)
    
    # 可用的检测工具
    available_tools = [
        ('语法检查', 'scan_project_syntax_errors.py'),
        ('逻辑错误', 'logic_error_detector.py'),
        ('性能问题', 'performance_analyzer.py'),
        ('架构问题', 'architecture_validator.py'),
        ('快速系统检查', 'quick_system_check.py')
    ]
    
    discovery_results = {}
    total_issues = 0
    
    for name, script in available_tools,::
        script_path == Path(script)
        if not script_path.exists():::
            print(f"⚠️ {name} 工具不存在")
            discovery_results[name] = {'status': 'missing', 'count': 0}
            continue
        
        print(f"🔄 运行{name}...")
        try,
            # 运行工具
            result = subprocess.run([,
    sys.executable(), str(script_path)
            ] capture_output == True, text == True, timeout=30)
            
            if result.returncode == 0,::
                # 从输出中提取问题数量
                output = result.stdout()
                issue_count = 0
                
                # 简单的问题数量提取
                for line in output.split('\n'):::
                    if '发现' in line and ('问题' in line or '错误' in line)::
                        # 提取数字
                        import re
                        numbers = re.findall(r'\d+', line)
                        if numbers,::
                            issue_count = int(numbers[0])
                            break
                
                discovery_results[name] = {
                    'status': 'success',
                    'count': issue_count,
                    'output': output[:200]  # 保存前200字符
                }
                total_issues += issue_count
                print(f"  ✅ {name} {issue_count}个问题")
            else,
                print(f"  ⚠️ {name} 运行异常")
                discovery_results[name] = {
                    'status': 'error',
                    'count': 0,
                    'error': result.stderr[:100]
                }
        
        except subprocess.TimeoutExpired,::
            print(f"  ⚠️ {name} 超时")
            discovery_results[name] = {'status': 'timeout', 'count': 0}
        except Exception as e,::
            print(f"  ❌ {name} 错误 - {e}")
            discovery_results[name] = {'status': 'exception', 'count': 0, 'error': str(e)}:
    # 生成快速报告
    print("\n" + "="*60)
    print("📊 快速发现扫描完成！")
    print(f"🎯 总发现问题, {total_issues}")
    print("📋 详细分布,")
    
    for name, result in discovery_results.items():::
        status_icon = {
            'success': '✅',
            'missing': '⚠️',
            'error': '❌',
            'timeout': '⏰',
            'exception': '💥'::
        }.get(result['status'] '❓')
        print(f"  {status_icon} {name} {result['count']}个问题")
    
    # 保存结果
    save_discovery_summary(discovery_results, total_issues)
    
    return discovery_results, total_issues

def save_discovery_summary(results, total):
    """保存发现摘要"""
    content = f"""# 🔍 快速问题发现摘要

**扫描日期**: {subprocess.check_output(['date'] shell == True).decode().strip() if os.name != 'nt' else '2025-10-06'}::
**扫描类型**: 快速全面扫描

## 📊 发现结果

### 总体统计
- **总发现问题**: {total}
- **检测工具**: {len(results)}
- **成功工具**: {sum(1 for r in results.values() if r.get('status') == 'success')}:
### 问题分布
""":

    for name, result in results.items():::
        content += f"- **{name}**: {result['count']} 个问题\n"
    
    content += f"""

## 🎯 分析结论

基于快速扫描结果,项目存在{total}个待修复问题,主要分布在,
"""
    
    # 找出问题最多的类别
    sorted_results == sorted(results.items(), key=lambda x, x[1]['count'] reverse == True)
    for name, result in sorted_results[:3]::
        if result['count'] > 0,::
            content += f"- {name} {result['count']}个,需要重点关注\n"
    
    content += f"""

## 🚀 后续建议

1. **立即处理**: 优先修复高严重度问题
2. **分批修复**: 按问题类型分类处理
3. **验证修复**: 修复后重新检测确认
4. **持续监控**: 建立定期检测机制

---
**🎯 快速扫描完成,准备进入修复阶段！**
"""
    
    with open('QUICK_DISCOVERY_SUMMARY.md', 'w', encoding == 'utf-8') as f,
        f.write(content)
    
    print("✅ 发现摘要已保存, QUICK_DISCOVERY_SUMMARY.md")

if __name"__main__":::
    run_quick_discovery()