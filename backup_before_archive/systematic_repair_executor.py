#!/usr/bin/env python3
"""
系统性修复执行脚本
按照PROJECT_SELF_HEALING_PLAN.md执行第三阶段的剩余工作
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

def check_directory_syntax(directory):
    """检查目录的语法状态"""
    print(f"正在检查 {directory} 目录的语法状态...")
    
    result = subprocess.run([
        sys.executable, '-m', 'py_compile',
        '-q',
        str(directory)
    ], capture_output=True, text=True, cwd='.')
    
    if result.returncode == 0:
        print(f"✅ {directory}目录: 未发现语法错误")
        return True
    else:
        print(f"❌ {directory}目录: 发现语法错误")
        if result.stderr:
            print("错误详情（前500字符）:", result.stderr[:500])
        return False

def count_python_files(directory):
    """统计目录中的Python文件数量"""
    py_files = list(Path(directory).rglob('*.py'))
    return len(py_files)

def fix_with_autopep8_batch(directory, batch_size=10):
    """使用autopep8分批修复目录中的文件"""
    print(f"\n🚀 开始对{directory}进行分批修复...")
    
    py_files = list(Path(directory).rglob('*.py'))
    total_files = len(py_files)
    
    print(f"📊 发现 {total_files} 个Python文件")
    
    fixed_count = 0
    error_count = 0
    
    # 分批处理
    for i in range(0, total_files, batch_size):
        batch_files = py_files[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total_files + batch_size - 1) // batch_size
        
        print(f"\n📦 处理第 {batch_num}/{total_batches} 批（{len(batch_files)} 个文件）")
        
        for file_path in batch_files:
            print(f"  修复: {file_path}")
            
            try:
                # 首先检查文件语法
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                # 如果文件已经语法正确，跳过
                compile(code, str(file_path), 'exec')
                print(f"    ✓ 文件语法正确，跳过")
                continue
                
            except SyntaxError:
                print(f"    🛠️ 发现语法错误，开始修复")
                
                try:
                    # 使用autopep8进行修复
                    result = subprocess.run([
                        sys.executable, '-m', 'autopep8',
                        '--in-place',
                        '--aggressive',
                        '--max-line-length=120',
                        str(file_path)
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        # 验证修复结果
                        with open(file_path, 'r', encoding='utf-8') as f:
                            new_code = f.read()
                        
                        try:
                            compile(new_code, str(file_path), 'exec')
                            print(f"    ✅ autopep8修复成功")
                            fixed_count += 1
                        except SyntaxError:
                            print(f"    ⚠️  autopep8修复后仍有语法错误")
                            error_count += 1
                    else:
                        print(f"    ❌ autopep8修复失败: {result.stderr}")
                        error_count += 1
                        
                except Exception as e:
                    print(f"    ❌ 修复异常: {e}")
                    error_count += 1
        
        print(f"  📊 第{batch_num}批完成：修复 {fixed_count} 个，失败 {error_count} 个")
        
        # 每批处理后暂停一下，避免系统过载
        if i + batch_size < total_files:
            print("  ⏱️  等待2秒继续下一批...")
            import time
            time.sleep(2)
    
    print(f"\n📈 {directory}修复统计:")
    print(f"  总文件数: {total_files}")
    print(f"  成功修复: {fixed_count}")
    print(f"  修复失败: {error_count}")
    print(f"  跳过文件: {total_files - fixed_count - error_count}")
    
    return fixed_count, error_count

def run_regression_test():
    """运行回归测试"""
    print("\n🧪 运行回归测试验证修复结果...")
    
    result = subprocess.run([
        sys.executable, '-m', 'pytest',
        'auto_fix_system_tests/test_basic_system.py',
        'auto_fix_system_tests/test_core_functions.py',
        '-v', '--tb=short'
    ], capture_output=True, text=True, cwd='.')
    
    if result.returncode == 0:
        print("✅ 回归测试通过！所有核心功能正常")
        return True
    else:
        print("❌ 回归测试失败")
        print("测试输出:", result.stdout[-500:])  # 显示最后500字符
        return False

def main():
    """主函数"""
    print("=" * 70)
    print("PROJECT_SELF_HEALING_PLAN - 第三阶段系统性修复")
    print(f"开始时间: {datetime.now()}")
    print("=" * 70)
    
    # 第一阶段：检查核心模块
    directories_to_fix = [
        'apps/backend/src/core',
        'apps/backend/src/ai',
        'apps/backend/src/services',
        'packages'
    ]
    
    total_fixed = 0
    total_errors = 0
    
    for directory in directories_to_fix:
        if Path(directory).exists():
            print(f"\n{'='*50}")
            print(f"📁 处理目录: {directory}")
            print(f"{'='*50}")
            
            # 检查语法状态
            syntax_ok = check_directory_syntax(directory)
            
            if not syntax_ok:
                # 统计文件数量
                file_count = count_python_files(directory)
                print(f"📊 发现 {file_count} 个Python文件")
                
                # 分批修复
                fixed, errors = fix_with_autopep8_batch(directory, batch_size=5)
                total_fixed += fixed
                total_errors += errors
            else:
                print(f"✅ {directory} 语法状态良好，跳过修复")
        else:
            print(f"⚠️  目录 {directory} 不存在，跳过")
    
    print(f"\n{'='*70}")
    print("📊 总体修复统计:")
    print(f"  成功修复: {total_fixed} 个文件")
    print(f"  修复失败: {total_errors} 个文件")
    print(f"  总计处理: {total_fixed + total_errors} 个文件")
    
    # 运行回归测试
    print(f"\n{'='*70}")
    test_passed = run_regression_test()
    
    print(f"\n{'='*70}")
    print("🎯 修复执行总结:")
    if total_fixed > 0:
        print(f"✅ 成功修复 {total_fixed} 个文件的语法错误")
    if total_errors > 0:
        print(f"⚠️  {total_errors} 个文件修复失败，需要手动处理")
    if test_passed:
        print("✅ 回归测试通过，系统功能正常")
    else:
        print("❌ 回归测试失败，需要进一步调试")
    
    print(f"\n⏰ 完成时间: {datetime.now()}")
    print("🎉 第三阶段系统性修复执行完成！")
    print("=" * 70)

if __name__ == "__main__":
    main()
