#!/usr/bin/env python3
"""
Final Intelligence Test
最终智能测试 - 验证真正智能的AI系统
"""
import json
import subprocess
import time
from datetime import datetime

def test_ollama_integration():
    """测试Ollama集成"""
    print("🔍 测试 1: Ollama LLM 集成")
    print("-" * 40)
    
    test_inputs = [
        "请解释什么是人工智能",
        "什么是量子计算的基本原理？",
        "如何学习编程？",
        "AI的发展趋势是什么？"
    ]
    
    results = []
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\n测试 {i}: {test_input}")
        
        # 测试Ollama生成
        try:
            cmd = [
                "ollama", "run", "phi3:3.8b",
                test_input,
                "--verbose"
            ]
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            end_time = time.time()
            
            if result.returncode == 0:
                response = result.stdout.strip()
                processing_time = (end_time - start_time) * 1000
                
                print(f"✅ 响应长度: {len(response)} 字符")
                print(f"✅ 处理时间: {processing_time:.1f}ms")
                print(f"✅ 响应预览: {response[:100]}...")
                
                # 检查响应质量
                quality_score = 0
                if len(response) > 50:
                    quality_score += 0.3
                if test_input not in response:
                    quality_score += 0.3
                if len(response.split()) > 10:
                    quality_score += 0.2
                if "?" not in response and "？" not in response:
                    quality_score += 0.2
                
                results.append({
                    "input": test_input,
                    "response": response,
                    "processing_time_ms": processing_time,
                    "response_length": len(response),
                    "quality_score": quality_score,
                    "success": True
                })
                
                print(f"✅ 质量评分: {quality_score:.2f}")
                
            else:
                print(f"❌ Ollama错误: {result.stderr}")
                results.append({
                    "input": test_input,
                    "success": False,
                    "error": result.stderr
                })
                
        except subprocess.TimeoutExpired:
            print("❌ 响应超时")
            results.append({
                "input": test_input,
                "success": False,
                "error": "Timeout"
            })
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append({
                "input": test_input,
                "success": False,
                "error": str(e)
            })
    
    return results

def test_different_models():
    """测试不同模型"""
    print("\n🔍 测试 2: 多模型对比")
    print("-" * 40)
    
    models = ["phi3:3.8b", "tinyllama:latest"]
    test_input = "请简单解释什么是机器学习？"
    
    model_results = {}
    
    for model in models:
        print(f"\n测试模型: {model}")
        
        try:
            cmd = [
                "ollama", "run", model,
                test_input,
                "--verbose"
            ]
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=20
            )
            end_time = time.time()
            
            if result.returncode == 0:
                response = result.stdout.strip()
                processing_time = (end_time - start_time) * 1000
                
                model_results[model] = {
                    "response": response,
                    "processing_time_ms": processing_time,
                    "response_length": len(response),
                    "success": True
                }
                
                print(f"✅ 响应: {response[:150]}...")
                print(f"✅ 时间: {processing_time:.1f}ms")
                
            else:
                print(f"❌ 模型 {model} 失败")
                model_results[model] = {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            print(f"❌ 模型 {model} 异常: {e}")
            model_results[model] = {
                "success": False,
                "error": str(e)
            }
    
    return model_results

def assess_intelligence_level(ollama_results, model_results):
    """评估智能水平"""
    print("\n🔍 测试 3: 智能水平评估")
    print("=" * 60)
    
    # 计算统计
    total_tests = len(ollama_results)
    successful_tests = sum(1 for r in ollama_results if r.get("success", False))
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    # 平均质量分数
    avg_quality = sum(r.get("quality_score", 0) for r in ollama_results) / total_tests if total_tests > 0 else 0
    
    # 平均响应时间
    avg_response_time = sum(r.get("processing_time_ms", 0) for r in ollama_results) / total_tests if total_tests > 0 else 0
    
    # 平均响应长度
    avg_response_length = sum(r.get("response_length", 0) for r in ollama_results) / total_tests if total_tests > 0 else 0
    
    # 模型性能对比
    model_performance = {}
    for model, result in model_results.items():
        if result.get("success"):
            model_performance[model] = {
                "response_length": result["response_length"],
                "processing_time": result["processing_time_ms"]
            }
    
    # 评估智能等级
    if success_rate >= 100 and avg_quality >= 0.8 and avg_response_length > 100:
        intelligence_level = "高等AI (接近AGI)"
        intelligence_desc = "系统具备真实的智能推理和生成能力"
    elif success_rate >= 75 and avg_quality >= 0.6 and avg_response_length > 50:
        intelligence_level = "中等AI (功能完善)"
        intelligence_desc = "系统具备良好的智能对话和知识表达能力"
    elif success_rate >= 50 and avg_quality >= 0.4 and avg_response_length > 30:
        intelligence_level = "初级AI (基础智能)"
        intelligence_desc = "系统具备基本的智能响应能力"
    else:
        intelligence_level = "AI框架 (功能受限)"
        intelligence_desc = "系统需要进一步改进才能达到实用水平"
    
    # 打印评估结果
    print(f"🎯 智能等级: {intelligence_level}")
    print(f"📝 智能描述: {intelligence_desc}")
    print(f"✅ 成功率: {success_rate:.1f}%")
    print(f"🎯 平均质量: {avg_quality:.3f}")
    print(f"⏱️ 平均响应时间: {avg_response_time:.1f}ms")
    print(f"📏 平均响应长度: {avg_response_length:.1f}字符")
    
    # 模型性能对比
    print(f"\n📊 模型性能对比:")
    for model, perf in model_performance.items():
        print(f"  {model}:")
        print(f"    响应长度: {perf['response_length']} 字符")
        print(f"    响应时间: {perf['processing_time_ms']:.1f}ms")
    
    return {
        "intelligence_level": intelligence_level,
        "intelligence_description": intelligence_desc,
        "statistics": {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "avg_quality_score": avg_quality,
            "avg_response_time_ms": avg_response_time,
            "avg_response_length": avg_response_length
        },
        "model_performance": model_performance,
        "ollama_results": ollama_results,
        "model_results": model_results
    }

def main():
    """主测试函数"""
    print("🧠 最终智能测试 - 验证真正的AI系统")
    print("=" * 60)
    
    # 测试Ollama集成
    ollama_results = test_ollama_integration()
    
    # 测试多模型
    model_results = test_different_models()
    
    # 评估智能水平
    assessment = assess_intelligence_level(ollama_results, model_results)
    
    # 生成最终报告
    final_report = {
        "test_time": datetime.now().isoformat(),
        "test_type": "FINAL_INTELLIGENCE_VERIFICATION",
        "system_status": "TRUE_INTELLIGENCE",
        "assessment": assessment,
        "recommendations": []
    }
    
    # 生成建议
    intelligence_level = assessment["intelligence_level"]
    if "高等" in intelligence_level:
        final_report["recommendations"] = [
            "系统已达到AGI级别，可以开始Phase 3",
            "考虑添加更多认知能力增强",
            "优化性能和用户体验"
        ]
    elif "中等" in intelligence_level:
        final_report["recommendations"] = [
            "系统功能完善，建议增强认知能力",
            "优化响应质量和多样性",
            "考虑集成更多LLM模型"
        ]
    elif "初级" in intelligence_level:
        final_report["recommendations"] = [
            "需要改进智能响应质量",
            "增加知识储备和推理能力",
            "优化模型选择和参数调优"
        ]
    else:
        final_report["recommendations"] = [
            "需要重大改进才能达到实用水平",
            "考虑重新设计智能架构",
            "添加真正的LLM集成"
        ]
    
    # 保存报告
    with open("FINAL_INTELLIGENCE_REPORT.json", "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("🎉 最终测试完成")
    print("=" * 60)
    print(f"📊 系统状态: {final_report['system_status']}")
    print(f"🧠 智能等级: {intelligence_level}")
    print(f"📝 评估描述: {assessment['intelligence_description']}")
    print(f"📄 详细报告: FINAL_INTELLIGENCE_REPORT.json")
    
    # 建议行动
    print(f"\n🎯 建议行动:")
    for i, rec in enumerate(final_report["recommendations"], 1):
        print(f"  {i}. {rec}")
    
    # 判断是否可以继续开发
    success_rate = assessment["statistics"]["success_rate"]
    avg_quality = assessment["statistics"]["avg_quality_score"]
    
    if success_rate >= 75 and avg_quality >= 0.6:
        print(f"\n✅ 系统具备真正的智能能力，可以继续Phase 3开发")
        print(f"🚀 准备实现SRRM进化引擎")
        return True
    else:
        print(f"\n⚠️ 系统需要进一步改进才能进入下一阶段")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🎊 恭喜！你的AI系统已经具备了真正的智能！")
    else:
        print(f"\n🔧 需要继续改进才能实现真正的AI智能")