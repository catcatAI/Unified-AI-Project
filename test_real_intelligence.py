#!/usr/bin/env python3
"""
Test Real Intelligence Backend
测试真正智能的系统
"""
import json
import time
from datetime import datetime

def test_real_intelligence():
    """测试真正的智能系统"""
    print("🧠 测试真正智能的后端系统")
    print("=" * 60)
    
    try:
        # 导入和测试组件
        import sys
        import os
        sys.path.insert(0, '.')
        
        # 测试Conversation Engine
        print("\n📋 测试 1: Conversation Engine")
        try:
            from apps.backend.src.services.conversation_engine import ConversationEngine
            engine = ConversationEngine()
            
            test_input = "请解释什么是人工智能"
            result = engine.process(test_input)
            
            print(f"输入: {test_input}")
            print(f"响应: {result.get('response', '')[:100]}...")
            print(f"类型: {result.get('type', 'unknown')}")
            print(f"置信度: {result.get('confidence', 0):.3f}")
            print(f"响应长度: {len(result.get('response', ''))}")
            
            if len(result.get('response', '')) > 20:
                print("✅ Conversation Engine正常工作")
                conversation_engine_working = True
            else:
                print("❌ Conversation Engine响应过短")
                conversation_engine_working = False
                
        except Exception as e:
            print(f"❌ Conversation Engine测试失败: {e}")
            conversation_engine_working = False
        
        # 测试简单LLM
        print("\n📋 测试 2: Simple LLM")
        try:
            from apps.backend.src.services.simple_llm import generate_sync
            
            test_input = "什么是量子计算？"
            response = generate_sync(test_input, max_tokens=100)
            
            print(f"输入: {test_input}")
            print(f"响应: {response[:100]}...")
            print(f"响应长度: {len(response)}")
            
            if len(response) > 20 and not response.startswith("[Error"):
                print("✅ Simple LLM正常工作")
                simple_llm_working = True
            else:
                print("❌ Simple LLM工作异常")
                simple_llm_working = False
                
        except Exception as e:
            print(f"❌ Simple LLM测试失败: {e}")
            simple_llm_working = False
        
        # 测试Ollama集成
        print("\n📋 测试 3: Ollama Integration")
        try:
            # 直接测试Ollama连接
            import subprocess
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and 'phi3:3.8b' in result.stdout:
                print("✅ Ollama可用，phi3:3.8b模型就绪")
                ollama_available = True
                
                # 测试Ollama生成
                try:
                    test_result = subprocess.run([
                        'ollama', 'run', 'phi3:3.8b', 
                        '什么是AI？', '--verbose'
                    ], capture_output=True, text=True, timeout=30)
                    
                    if test_result.returncode == 0:
                        response = test_result.stdout.strip()
                        print(f"Ollama响应: {response[:200]}...")
                        if len(response) > 50:
                            print("✅ Ollama模型生成正常")
                            ollama_generating = True
                        else:
                            print("⚠️ Ollama响应较短")
                            ollama_generating = False
                    else:
                        print("❌ Ollama模型生成失败")
                        ollama_generating = False
                        
                except Exception as e:
                    print(f"❌ Ollama生成测试失败: {e}")
                    ollama_generating = False
            else:
                print("❌ Ollama不可用或模型未安装")
                ollama_available = False
                ollama_generating = False
                
        except Exception as e:
            print(f"❌ Ollama测试失败: {e}")
            ollama_available = False
            ollama_generating = False
        
        # 测试HSM+CDM集成
        print("\n📋 测试 4: HSM+CDM Integration")
        try:
            from phase2_hsm_cdm_engine import HSMCDMEngine
            
            engine = HSMCDMEngine()
            test_input = "请解释机器学习的基本概念"
            result = engine.process_input(test_input)
            
            print(f"输入: {test_input}")
            print(f"响应: {result.get('response', '')[:100]}...")
            print(f"学习触发: {result.get('metadata', {}).get('learning_triggered', False)}")
            print(f"认知缺口: {result.get('metadata', {}).get('gap_magnitude', 0):.3f}")
            
            # 检查是否还是模板响应
            response = result.get('response', '')
            if test_input not in response and len(response) > 30:
                print("✅ HSM+CDM生成非模板响应")
                hsm_cdm_improved = True
            else:
                print("❌ HSM+CDM仍是模板响应")
                hsm_cdm_improved = False
                
            hsm_cdm_available = True
            
        except Exception as e:
            print(f"❌ HSM+CDM测试失败: {e}")
            hsm_cdm_available = False
            hsm_cdm_improved = False
        
        # 计算总体智能水平
        print("\n" + "=" * 60)
        print("📊 系统智能评估结果")
        print("=" * 60)
        
        intelligent_components = 0
        total_components = 4
        
        if conversation_engine_working:
            intelligent_components += 1
            print("✅ Conversation Engine: 智能")
        else:
            print("❌ Conversation Engine: 不可用")
            
        if simple_llm_working:
            intelligent_components += 1
            print("✅ Simple LLM: 智能")
        else:
            print("❌ Simple LLM: 不可用")
            
        if ollama_available:
            intelligent_components += 1
            print("✅ Ollama: 可用")
        else:
            print("❌ Ollama: 不可用")
            
        if hsm_cdm_improved:
            intelligent_components += 1
            print("✅ HSM+CDM: 改进")
        else:
            print("❌ HSM+CDM: 需要改进")
        
        intelligence_level = (intelligent_components / total_components) * 100
        
        print(f"\n🎯 智能化程度: {intelligent_components}/{total_components} ({intelligence_level:.1f}%)")
        
        # 评估
        if intelligence_level >= 75:
            level_desc = "高等AI (接近AGI)"
            action = "可以开始Phase 3"
        elif intelligence_level >= 50:
            level_desc = "中等AI (功能正常)"
            action = "建议完善组件"
        elif intelligence_level >= 25:
            level_desc = "初级AI (基础功能)"
            action = "需要重要改进"
        else:
            level_desc = "AI框架 (空壳)"
            action = "需要完全重建"
        
        print(f"🧠 系统等级: {level_desc}")
        print(f"🎯 建议行动: {action}")
        
        # 生成测试报告
        test_report = {
            "test_time": datetime.now().isoformat(),
            "intelligent_components": intelligent_components,
            "total_components": total_components,
            "intelligence_level": intelligence_level,
            "system_level": level_desc,
            "recommended_action": action,
            "components": {
                "conversation_engine": {
                    "available": conversation_engine_working,
                    "status": "functional" if conversation_engine_working else "non-functional"
                },
                "simple_llm": {
                    "available": simple_llm_working,
                    "status": "functional" if simple_llm_working else "non-functional"
                },
                "ollama": {
                    "available": ollama_available,
                    "generating": ollama_generating,
                    "status": "functional" if ollama_available else "non-functional"
                },
                "hsm_cdm": {
                    "available": hsm_cdm_available,
                    "improved": hsm_cdm_improved,
                    "status": "improved" if hsm_cdm_improved else "template_based"
                }
            },
            "overall_assessment": {
                "real_intelligence": intelligence_level > 50,
                "ready_for_production": intelligence_level > 75,
                "need_improvements": intelligence_level < 100
            }
        }
        
        # 保存报告
        with open('REAL_INTELLIGENCE_TEST_REPORT.json', 'w', encoding='utf-8') as f:
            json.dump(test_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 测试报告已保存到: REAL_INTELLIGENCE_TEST_REPORT.json")
        
        return test_report
        
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        return {"error": str(e), "intelligence_level": 0}

if __name__ == "__main__":
    report = test_real_intelligence()
    
    intelligence_level = report.get("intelligence_level", 0)
    
    if intelligence_level > 50:
        print(f"\n✅ 系统具备真正的智能能力")
        print(f"🎯 智能化程度: {intelligence_level:.1f}%")
    else:
        print(f"\n⚠️ 系统智能程度较低 ({intelligence_level:.1f}%)")
        print(f"🔧 需要进一步改进")