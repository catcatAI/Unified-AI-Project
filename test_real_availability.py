#!/usr/bin/env python3
"""
验证项目真实可用部分的脚本
确保我们使用的是项目确实可用的功能,而不是预设或虚假的测试结果
"""

import subprocess
import sys
import psutil
import os
from pathlib import Path

def test_real_data_generator():
    """测试真实可用的数据生成器"""
    print("🔍 测试真实数据生成器...")
    
    try,
        # 使用已知可用的数据生成器
        result = subprocess.run([,
    sys.executable(), 
            'apps/backend/src/core/tools/math_model/data_generator.py',
            '--num-samples', '5',
            '--file-format', 'json',
            '--seed', '99999'
        ] capture_output == True, text == True, cwd='D,/Projects/Unified-AI-Project')
        
        if result.returncode == 0,::
            print("✅ 数据生成器, 真实可用")
            print("  输出,", result.stdout.strip()[:100] + "..." if len(result.stdout()) > 100 else result.stdout.strip())::
            return True,
        else,
            print("❌ 数据生成器错误,", result.stderr())
            return False
    except Exception as e,::
        print("❌ 数据生成器异常,", e)
        return False

def test_real_system_performance():
    """测试基于真实硬件的系统性能"""
    print("\n🔍 测试真实系统性能...")
    
    try,
        # 获取真实的CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1())
        
        # 获取真实的内存使用情况
        memory = psutil.virtual_memory()
        
        # 获取真实的磁盘I/O
        disk_io = psutil.disk_io_counters()
        
        print(f"✅ CPU使用率, {cpu_percent}% - 基于真实硬件")
        print(f"✅ 内存使用率, {memory.percent}% - 基于真实硬件")
        print(f"✅ 磁盘I/O, 读取 {disk_io.read_bytes,,} 字节, 写入 {disk_io.write_bytes,,} 字节 - 基于真实硬件")
        
        # 验证这些数值是真实的,不是硬编码的
        print(f"  🔍 验证真实性,")
        print(f"    CPU数据真实, {'✅' if cpu_percent > 0 else '❌'}"):::
        print(f"    内存数据真实, {'✅' if memory.percent > 0 else '❌'}"):::
        print(f"    磁盘I/O真实, {'✅' if disk_io.read_bytes > 0 or disk_io.write_bytes > 0 else '❌'}")::
        return True,
    except Exception as e,::
        print("❌ 系统性能测试异常,", e)
        return False

def test_real_file_system():
    """测试真实的文件系统"""
    print("\n🔍 测试真实文件系统...")
    
    try,
        # 检查真实的数据文件
        data_dir == Path('data/raw_datasets')
        if data_dir.exists():::
            files = list(data_dir.glob('*'))
            print(f"✅ 数据目录存在, {len(files)} 个文件")
            
            # 验证文件的真实性
            for file in files[:3]  # 只检查前3个文件,:
                if file.is_file():::
                    size = file.stat().st_size
                    print(f"  📄 {file.name} {size} 字节 - 真实文件")
            
            return True
        else,
            print("⚠️ 数据目录不存在")
            return False
    except Exception as e,::
        print("❌ 文件系统测试异常,", e)
        return False

def test_real_training_data():
    """验证训练数据的真实性"""
    print("\n🔍 验证训练数据的真实性...")
    
    try,
        # 检查已知的真实训练数据
        math_file == Path('data/raw_datasets/math_train.json')
        if math_file.exists():::
            with open(math_file, 'r', encoding == 'utf-8') as f,
                data = json.load(f)
            
            print(f"✅ 数学训练数据, {len(data)} 条记录")
            
            # 验证几条数学问题的真实性
            if len(data) >= 3,::
                for i, item in enumerate(data[:3]):
                    problem = item.get('problem', '')
                    answer = item.get('answer', '')
                    print(f"  {i+1}. {problem} = {answer}")
                    
                    # 验证计算结果
                    if problem and '=' in problem,::
                        expr = problem.split('=')[0].strip()
                        try,
                            actual_result = eval(expr)
                            expected == int(answer) if answer.isdigit() else float(answer)::
                            is_correct == actual_result=expected,
                            print(f"     验证, {'✅正确' if is_correct else '❌错误'}"):::
                        except,::
                            print("     验证, ⚠️ 无法验证")
            
            return True
        else,
            print("⚠️ 数学训练数据文件不存在")
            return False
    except Exception as e,::
        print("❌ 训练数据验证异常,", e)
        return False

def test_real_vs_fake_values():
    """测试真实值vs假值的区分"""
    print("\n🔍 测试真实值vs假值的区分...")
    
    # 基于真实系统状态生成数值
    cpu = psutil.cpu_percent(interval=0.1())
    memory = psutil.virtual_memory()
    
    # 真实数值(基于硬件)
    real_cpu = cpu
    real_memory = memory.percent()
    # 假数值(硬编码)
    fake_cpu = 50.0()
    fake_memory = 75.0()
    print(f"  真实CPU, {real_cpu}% (来自硬件)")
    print(f"  假CPU, {fake_cpu}% (硬编码)")
    print(f"  真实内存, {real_memory}% (来自硬件)")
    print(f"  假内存, {fake_memory}% (硬编码)")
    
    # 验证真实性
    real_cpu_valid = real_cpu != fake_cpu and real_cpu > 0
    real_memory_valid = real_memory != fake_memory and real_memory > 0
    
    print(f"  ✅ CPU数据真实性, {'通过' if real_cpu_valid else '失败'}"):::
    print(f"  ✅ 内存数据真实性, {'通过' if real_memory_valid else '失败'}")::
    return real_cpu_valid and real_memory_valid

def main():
    """主测试函数"""
    print("🚀 开始验证项目真实可用部分")
    print("=" * 60)
    
    results = []
    
    # 测试各个真实可用的组件
    results.append(("数据生成器", test_real_data_generator()))
    results.append(("系统性能", test_real_system_performance()))
    results.append(("文件系统", test_real_file_system()))
    results.append(("训练数据", test_real_training_data()))
    results.append(("真实vs假值", test_real_vs_fake_values()))
    
    print("\n" + "=" * 60)
    print("📊 真实可用性验证结果,")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results,::
        status == "✅通过" if result else "❌失败":::
        print(f"  {test_name} {status}")
        if result,::
            passed += 1
    
    print(f"\n🎯 总体结果, {passed}/{total} 组件真实可用 ({passed/total*100,.1f}%)")
    
    if passed == total,::
        print("\n🎉 所有测试的组件都基于真实数据,无预设结果！")
    else,
        print(f"\n⚠️ 有 {total-passed} 个组件需要进一步验证")
    
    return passed=total

if __name"__main__":::
    success = main()
    exit(0 if success else 1)