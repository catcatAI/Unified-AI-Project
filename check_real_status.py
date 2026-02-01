#!/usr/bin/env python3
"""
Real-time System Status Check
实时检查系统真实状态
"""
import subprocess
import time
import json
from datetime import datetime

def clean_ollama_output(output):
    """清理Ollama输出的控制字符"""
    import re
    # 移除ANSI控制字符
    clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)
    # 移除零字符
    clean = clean.replace('\x00', '')
    return clean.strip()

def test_ollama_real():
    """测试Ollama真实响应"""
    print("🔍 实时Ollama测试")
    print("=" * 50)
    
    test_cases = [
        "你好",
        "什么是AI？", 
        "简单解释机器学习",
        "量子计算是什么？"
    ]
    
    results = []
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test_input}")
        
        try:
            # 使用--format json获取干净输出
            cmd = [
                "ollama", "run", "phi3:3.8b", 
                test_input,
                "--format", "json"
            ]
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            end_time = time.time()
            
            if result.returncode == 0:
                raw_output = result.stdout.strip()
                cleaned_output = clean_ollama_output(raw_output)
                processing_time = (end_time - start_time) * 1000
                
                # 尝试解析JSON
                response = cleaned_output
                try:
                    parsed = json.loads(cleaned_output)
                    if isinstance(parsed, dict) and 'response' in parsed:
                        response = parsed['response']
                except:
                    pass
                
                print(f"✅ 成功: {len(response)} 字符")
                print(f"⏱️  时间: {processing_time:.1f}ms")
                print(f"📝 响应: {response[:100]}...")
                
                # 检查是否是智能响应
                is_intelligent = (
                    len(response) > 30 and
                    test_input not in response and
                    not "请" in response[:10]  # 避免模板开头
                )
                
                results.append({
                    "input": test_input,
                    "response": response,
                    "processing_time_ms": processing_time,
                    "response_length": len(response),
                    "is_intelligent": is_intelligent,
                    "success": True
                })
                
                status = "🧠 智能响应" if is_intelligent else "📝 基础响应"
                print(f"🎯 评估: {status}")
                
            else:
                error_output = clean_ollama_output(result.stderr)
                print(f"❌ 失败: {error_output}")
                results.append({
                    "input": test_input,
                    "success": False,
                    "error": error_output
                })
                
        except subprocess.TimeoutExpired:
            print("❌ 超时")
            results.append({
                "input": test_input,
                "success": False,
                "error": "Timeout"
            })
        except Exception as e:
            print(f"❌ 异常: {e}")
            results.append({
                "input": test_input,
                "success": False,
                "error": str(e)
            })
    
    return results

def test_conversation_engine():
    """测试对话引擎"""
    print("\n🔍 对话引擎测试")
    print("=" * 50)
    
    try:
        # 测试导入
        import sys
        import os
        sys.path.insert(0, '.')
        
        from apps.backend.src.services.conversation_engine import ConversationEngine
        engine = ConversationEngine()
        
        test_input = "请解释什么是人工智能"
        result = engine.process(test_input)
        
        response = result.get('response', '')
        print(f"输入: {test_input}")
        print(f"响应: {response[:100]}...")
        print(f"长度: {len(response)} 字符")
        print(f"类型: {result.get('type', 'unknown')}")
        
        is_working = len(response) > 20
        status = "✅ 正常工作" if is_working else "❌ 响应过短"
        print(f"状态: {status}")
        
        return {
            "success": is_working,
            "response": response,
            "response_length": len(response),
            "type": result.get('type', 'unknown')
        }
        
    except Exception as e:
        print(f"❌ 对话引擎失败: {e}")
        return {"success": False, "error": str(e)}

def assess_current_system():
    """评估当前系统状态"""
    print("\n" + "=" * 60)
    print("🎯 当前系统真实状态评估")
    print("=" * 60)
    
    # 测试Ollama
    ollama_results = test_ollama_real()
    
    # 测试对话引擎
    conversation_result = test_conversation_engine()
    
    # 统计Ollama结果
    successful_tests = sum(1 for r in ollama_results if r.get("success", False))
    intelligent_responses = sum(1 for r in ollama_results if r.get("is_intelligent", False))
    total_tests = len(ollama_results)
    
    ollama_success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    ollama_intelligence_rate = (intelligent_responses / total_tests) * 100 if total_tests > 0 else 0
    
    avg_response_length = sum(r.get("response_length", 0) for r in ollama_results) / total_tests if total_tests > 0 else 0
    avg_processing_time = sum(r.get("processing_time_ms", 0) for r in ollama_results) / total_tests if total_tests > 0 else 0
    
    # 整体系统评估
    print(f"\n📊 Ollama 系统评估:")
    print(f"  成功率: {ollama_success_rate:.1f}% ({successful_tests}/{total_tests})")
    print(f"  智能率: {ollama_intelligence_rate:.1f}% ({intelligent_responses}/{total_tests})")
    print(f"  平均长度: {avg_response_length:.1f} 字符")
    print(f"  平均时间: {avg_processing_time:.1f}ms")
    
    print(f"\n📊 对话引擎评估:")
    if conversation_result.get("success", False):
        print(f"  状态: ✅ 可用")
        print(f"  响应长度: {conversation_result.get('response_length', 0)} 字符")
    else:
        print(f"  状态: ❌ 不可用")
    
    # 最终智能等级
    print(f"\n🎯 系统智能等级:")
    
    if ollama_success_rate >= 75 and ollama_intelligence_rate >= 50:
        intelligence_level = "高等AI"
        description = "系统具备真实的智能生成和推理能力"
        ready_for_next = True
    elif ollama_success_rate >= 50 and avg_response_length > 30:
        intelligence_level = "中等AI"
        description = "系统具备基本的智能响应能力"
        ready_for_next = False
    elif ollama_success_rate >= 25:
        intelligence_level = "初级AI"
        description = "系统具备有限的智能功能"
        ready_for_next = False
    else:
        intelligence_level = "AI框架"
        description = "系统需要重大改进"
        ready_for_next = False
    
    print(f"  等级: {intelligence_level}")
    print(f"  描述: {description}")
    print(f"  准备下一阶段: {'✅ 是' if ready_for_next else '❌ 否'}")
    
    # 生成状态报告
    status_report = {
        "check_time": datetime.now().isoformat(),
        "system_status": "REAL_INTELLIGENCE_CHECK",
        "ollama": {
            "success_rate": ollama_success_rate,
            "intelligence_rate": ollama_intelligence_rate,
            "avg_response_length": avg_response_length,
            "avg_processing_time_ms": avg_processing_time,
            "test_results": ollama_results
        },
        "conversation_engine": conversation_result,
        "overall": {
            "intelligence_level": intelligence_level,
            "description": description,
            "ready_for_next_phase": ready_for_next,
            "real_intelligence": ollama_intelligence_rate > 50
        }
    }
    
    # 保存报告
    with open("CURRENT_REAL_STATUS_REPORT.json", "w", encoding="utf-8") as f:
        json.dump(status_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 状态报告已保存: CURRENT_REAL_STATUS_REPORT.json")
    
    return status_report

def main():
    """主检查函数"""
    print("🔍 真实时系统状态检查")
    print("检查当前系统的真实智能能力...")
    
    status = assess_current_system()
    
    print("\n" + "=" * 60)
    print("🎉 系统状态检查完成")
    print("=" * 60)
    
    if status["overall"]["real_intelligence"]:
        print(f"🌟 系统具备真实的AI智能！")
        print(f"🧠 智能等级: {status['overall']['intelligence_level']}")
        print(f"🚀 可以继续开发Phase 3")
    else:
        print(f"⚠️ 系统智能程度需要改进")
        print(f"🔧 建议完善Ollama集成")
        print(f"📋 需要解决控制字符问题")
    
    return status["overall"]["real_intelligence"]

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n✅ 恭喜！你的AI系统确实具备真正的智能！")
        exit(0)
    else:
        print(f"\n🔧 系统需要进一步改进")
        exit(1)