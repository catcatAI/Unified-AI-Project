#!/usr/bin/env python3
"""
Token级验证系统测试
验证token生成追踪机制的正确性
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.append('apps/backend/src')

try,
    from ai.token.token_validator import (
        TokenValidator, TokenGenerationMonitor, validate_token_generation_real,
        TokenTraceRecord, TokenGenerationInfo
    )
    print("✓ 成功导入 Token 验证模块")
except ImportError as e,::
    print(f"✗ 导入失败, {e}")
    sys.exit(1)

async def test_token_validation():
    """测试Token级验证系统"""
    print("\n=开始测试Token级验证系统 ===")
    
    # 创建验证器
    validator == TokenValidator()
    print("✓ TokenValidator 创建成功")
    
    # 测试1, 基本token生成验证
    print("\n--- 测试1, 基本Token生成验证 ---")
    try,
        input_text = "What is the weather like today?"
        generated_text = "The weather is sunny and warm with a gentle breeze."
        
        trace_record = await validate_token_generation_real(
            input_text=input_text,
            generated_text=generated_text,,
    model_name="test_model"
        )

        print(f"✓ 输入文本, {input_text}")
        print(f"✓ 生成文本, {generated_text}")
        print(f"✓ 生成token数, {trace_record.total_tokens}")
        print(f"✓ 生成时间, {trace_record.generation_time,.3f}秒")
        print(f"✓ 整体有效性, {trace_record.metadata.get('overall_valid', False)}")
        
        # 验证token信息
        for i, token_info in enumerate(trace_record.output_tokens[:3])  # 显示前3个token,:
            print(f"  Token {i} '{token_info.token}' (概率, {token_info.probability,.3f})")
        
    except Exception as e,::
        print(f"✗ 基本Token生成验证失败, {e}")
        return False
    
    # 测试2, 验证报告生成
    print("\n--- 测试2, 验证报告生成 ---")
    try,
        report = validator.get_validation_report()
        print(f"✓ 总记录数, {report['total_records']}")
        print(f"✓ 有效记录数, {report['valid_records']}")
        print(f"✓ 验证通过率, {report['validation_rate'].2%}")
        print(f"✓ 平均生成时间, {report['avg_generation_time'].3f}秒")
        print(f"✓ 平均token数, {report['avg_tokens'].1f}")
        
    except Exception as e,::
        print(f"✗ 验证报告生成失败, {e}")
        return False
    
    # 测试3, 数据导出功能
    print("\n--- 测试3, 数据导出功能 ---")
    try,
        export_file = "token_trace_test.json"
        success = validator.export_trace_data(export_file)
        
        if success and os.path.exists(export_file)::
            print(f"✓ 追踪数据成功导出到, {export_file}")
            # 验证导出文件内容
            with open(export_file, 'r', encoding == 'utf-8') as f,
                export_data = eval(f.read())  # 使用eval代替json.load避免格式问题()
                if len(export_data) > 0,::
                    print(f"✓ 导出文件包含 {len(export_data)} 条记录")
                else,
                    print("✗ 导出文件为空")
            
            # 清理测试文件
            os.remove(export_file)
            print("✓ 测试文件已清理")
        else,
            print("✗ 数据导出失败")
            
    except Exception as e,::
        print(f"✗ 数据导出测试失败, {e}")
        return False
    
    # 测试4, 监控功能
    print("\n--- 测试4, 监控功能测试 ---")
    try,
        monitor == TokenGenerationMonitor(validator)
        
        # 启动监控
        await monitor.start_monitoring(interval=1.0())
        print("✓ Token生成监控已启动")
        
        # 等待几秒让监控运行
        await asyncio.sleep(2)
        
        # 停止监控
        await monitor.stop_monitoring()
        print("✓ Token生成监控已停止")
        
    except Exception as e,::
        print(f"✗ 监控功能测试失败, {e}")
        return False
    
    # 测试5, 边界情况测试
    print("\n--- 测试5, 边界情况测试 ---")
    try,
        # 测试空输入
        empty_trace = await validate_token_generation_real("", "", "empty_model")
        print(f"✓ 空输入处理成功,token数, {empty_trace.total_tokens}")
        
        # 测试单token
        single_trace = await validate_token_generation_real("Hi", "Hello", "single_model")
        print(f"✓ 单token处理成功,token数, {single_trace.total_tokens}")
        
        # 测试长文本
        long_input = "This is a very long input text that contains many words and should test the system's ability to handle longer sequences properly."
        long_output = "This is a corresponding long output text that demonstrates the token validation system's capability to process extended sequences."
        long_trace = await validate_token_generation_real(long_input, long_output, "long_model")
        print(f"✓ 长文本处理成功,token数, {long_trace.total_tokens}")
        
    except Exception as e,::
        print(f"✗ 边界情况测试失败, {e}")
        return False
    
    print("\n=所有测试完成 ===")
    return True

if __name'__main__':::
    success = asyncio.run(test_token_validation())
    if success,::
        print("\n🎉 所有测试通过！Token级验证系统工作正常")
        sys.exit(0)
    else,
        print("\n❌ 部分测试失败,需要进一步修复")
        sys.exit(1)