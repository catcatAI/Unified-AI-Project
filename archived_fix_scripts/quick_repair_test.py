import sys
sys.path.append('.')

from pathlib import Path

def quick_repair_test():
    """快速修复测试 - 选择几个核心文件"""
    
    # 选择几个核心Python文件进行修复测试
    test_files = [
        "apps/backend/src/core/hsp/__init__.py",
        "apps/backend/src/core/hsp/base_hsp.py", 
        "apps/backend/src/ai/memory/__init__.py",
        "unified_auto_fix_system/core/__init__.py"
    ]
    
    print("=== 快速修复测试 ===")
    print("选择核心Python文件进行修复测试\n")
    
    for file_path in test_files:
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"⚠️  文件不存在: {file_path}")
            continue
            
        print(f"\n📄 分析文件: {file_path}")
        
        # 使用命令行分析
        import subprocess
        cmd = f"python -m unified_auto_fix_system.main analyze --scope file --target {file_path} --format summary"
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                if "发现 0 个语法问题" in result.stdout:
                    print("  ✅ 文件健康，无需修复")
                else:
                    print(f"  🔍 发现问题，准备修复...")
                    
                    # 执行修复
                    repair_cmd = f"python -m unified_auto_fix_system.main fix --scope file --target {file_path}"
                    repair_result = subprocess.run(repair_cmd, shell=True, capture_output=True, text=True, timeout=60)
                    
                    if repair_result.returncode == 0:
                        print("  ✅ 修复完成")
                        
                        # 验证修复结果
                        verify_cmd = f"python -m unified_auto_fix_system.main analyze --scope file --target {file_path} --format summary"
                        verify_result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True, timeout=60)
                        
                        if verify_result.returncode == 0 and "发现 0 个语法问题" in verify_result.stdout:
                            print("  ✅ 验证通过，文件已修复")
                        else:
                            print("  ⚠️  验证结果不确定")
                    else:
                        print(f"  ❌ 修复失败: {repair_result.stderr}")
            else:
                print(f"  ❌ 分析失败: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"  ⏰ 分析超时，跳过此文件")
        except Exception as e:
            print(f"  ❌ 执行失败: {e}")

if __name__ == "__main__":
    quick_repair_test()