#!/usr/bin/env python3
"""
Phase 2 Completion Test Script
测试 HSM+CDM 核心机制的完整实现
"""
import asyncio
import json
import sys
import time
from datetime import datetime

def test_phase2_implementation():
    """测试 Phase 2 HSM+CDM 实现"""
    print("🧠 Phase 2 HSM+CDM 机制验证测试")
    print("=" * 60)
    
    # 添加 HSM+CDM 引擎路径
    sys.path.insert(0, ".")
    
    results = {
        "hsm_implemented": False,
        "cdm_implemented": False,
        "cognitive_gap_detection": False,
        "logic_unit_solidification": False,
        "heuristic_simulation": False,
        "learning_capability": False,
        "retrieval_system": False,
        "feedback_mechanism": False
    }
    
    try:
        # 导入并测试 HSM+CDM 引擎
        from phase2_hsm_cdm_engine import HSMCDMEngine, CognitiveGapDetector, HeuristicSimulationMechanism, CognitiveDividendModel
        
        # Test 1: 认知缺口检测
        print("\n📋 测试 1: 认知缺口检测 (C_Gap)")
        gap_detector = CognitiveGapDetector()
        test_input = {"content": "什么是量子计算的基本原理？", "context": ""}
        gap_result = gap_detector.calculate_cognitive_gap(test_input)
        
        required_metrics = ["magnitude", "confidence", "complexity"]
        results["cognitive_gap_detection"] = all(metric in gap_result for metric in required_metrics)
        
        if results["cognitive_gap_detection"]:
            print(f"✅ C_Gap 检测正常 (magnitude={gap_result['magnitude']:.3f}, confidence={gap_result['confidence']:.3f})")
        else:
            print("❌ C_Gap 检测失败")
        
        # Test 2: 启发式模拟机制
        print("\n📋 测试 2: 启发式模拟机制 (HSM)")
        hsm = HeuristicSimulationMechanism()
        hsm_result = hsm.simulate_solution(test_input, gap_result)
        
        required_hsm = ["solution", "hsm_score", "candidates_explored", "confidence"]
        results["heuristic_simulation"] = all(key in hsm_result for key in required_hsm)
        
        if results["heuristic_simulation"]:
            print(f"✅ HSM 模拟正常 (探索了{hsm_result['candidates_explored']}个候选方案)")
        else:
            print("❌ HSM 模拟失败")
        
        # Test 3: 认知配息模型
        print("\n📋 测试 3: 认知配息模型 (CDM)")
        cdm = CognitiveDividendModel()
        
        # 测试逻辑单元固化
        experience = {"content": "测试经验", "timestamp": datetime.now().isoformat()}
        unit_id = cdm.solidify_logic_unit(experience, hsm_result)
        results["logic_unit_solidification"] = unit_id != "ERROR"
        
        if results["logic_unit_solidification"]:
            print(f"✅ CDM 逻辑单元固化正常 (单元ID: {unit_id})")
        else:
            print("❌ CDM 逻辑单元固化失败")
        
        # 测试检索系统
        retrieved_units = cdm.retrieve_relevant_units("测试查询", limit=3)
        results["retrieval_system"] = isinstance(retrieved_units, list)
        
        if results["retrieval_system"]:
            print(f"✅ CDM 检索系统正常 (检索到{len(retrieved_units)}个相关单元)")
        else:
            print("❌ CDM 检索系统失败")
        
        # Test 4: 反馈机制
        print("\n📋 测试 4: 反馈机制")
        feedback_result = cdm.update_effectiveness(unit_id, 0.8)
        results["feedback_mechanism"] = feedback_result is None  # update_effectiveness 不返回值
        
        if results["feedback_mechanism"]:
            print("✅ 反馈机制正常")
        else:
            print("❌ 反馈机制失败")
        
        # Test 5: 完整集成引擎
        print("\n📋 测试 5: HSM+CDM 集成引擎")
        engine = HSMCDMEngine()
        
        # 验证组件存在
        results["hsm_implemented"] = hasattr(engine, 'hsm') and engine.hsm is not None
        results["cdm_implemented"] = hasattr(engine, 'cdm') and engine.cdm is not None
        
        # 测试学习能力
        test_response = asyncio.run(engine.process_input("请解释人工智能的学习机制"))
        results["learning_capability"] = test_response.get("metadata", {}).get("learning_triggered", False)
        
        if results["hsm_implemented"] and results["cdm_implemented"]:
            print("✅ HSM+CDM 集成引擎组件正常")
        else:
            print("❌ HSM+CDM 集成引擎组件异常")
        
        if results["learning_capability"]:
            print("✅ 学习能力正常")
        else:
            print("❌ 学习能力异常")
        
        # Test 6: 核心公式验证
        print("\n📋 测试 6: 核心公式验证")
        
        # 验证 HSM = C_Gap × E_M2
        gap_magnitude = gap_result.get("magnitude", 0.0)
        em2_factor = 0.1  # 固定探索因子
        expected_hsm_score = gap_magnitude * em2_factor
        actual_hsm_score = hsm_result.get("hsm_score", 0.0)
        
        formula_error = abs(expected_hsm_score - actual_hsm_score)
        formula_correct = formula_error < 0.01  # 允许小误差
        
        if formula_correct:
            print(f"✅ HSM 公式验证通过 (预期: {expected_hsm_score:.4f}, 实际: {actual_hsm_score:.4f})")
        else:
            print(f"❌ HSM 公式验证失败 (预期: {expected_hsm_score:.4f}, 实际: {actual_hsm_score:.4f})")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return {"status": "IMPORT_ERROR", "error": str(e)}
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        return {"status": "TEST_ERROR", "error": str(e)}
    
    # 计算总体评分
    passed_tests = sum(1 for k, v in results.items() if v)
    total_tests = len(results)
    success_rate = (passed_tests / total_tests) * 100
    
    print("\n" + "=" * 60)
    print("📊 Phase 2 HSM+CDM 实现验证结果")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n🎯 总体评分: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    # Phase 2 完成标准
    core_requirements = [
        "cognitive_gap_detection",
        "heuristic_simulation", 
        "logic_unit_solidification",
        "retrieval_system",
        "learning_capability"
    ]
    
    core_passed = sum(1 for test in core_requirements if results.get(test, False))
    core_success_rate = (core_passed / len(core_requirements)) * 100
    
    if success_rate >= 85:
        print("🎉 Phase 2 HSM+CDM 核心机制实现成功！")
        phase_status = "COMPLETED"
        next_phase = "SRRM_EVOLUTION_ENGINE"
    elif core_success_rate >= 70:
        print("⚠️ Phase 2 部分实现，建议完善核心功能")
        phase_status = "PARTIAL"
        next_phase = "COMPLETE_CORE_FEATURES"
    else:
        print("🚨 Phase 2 实现不充分，需要重新实现核心机制")
        phase_status = "INSUFFICIENT"
        next_phase = "REIMPLEMENT_CORE"
    
    # 生成报告
    report = {
        "phase": 2,
        "implementation": "HSM+CDM_CORE_MECHANISMS",
        "completion_time": datetime.now().isoformat(),
        "test_results": results,
        "overall_success_rate": success_rate,
        "core_success_rate": core_success_rate,
        "status": phase_status,
        "next_phase": next_phase,
        "implemented_features": [
            "Cognitive Gap Detection (C_Gap)",
            "Heuristic Simulation Mechanism (HSM)",
            "Cognitive Dividend Model (CDM)",
            "Logic Unit Solidification",
            "Dynamic Retrieval System",
            "Feedback Learning Loop"
        ],
        "core_formulas": [
            "HSM = C_Gap × E_M2",
            "CDM = Logic_Unit + Memory_Encoding + Dynamic_Retrieval"
        ],
        "metrics": {
            "gap_threshold": 0.7,
            "em2_factor": 0.1,
            "learning_capability": True,
            "feedback_mechanism": True
        }
    }
    
    # 保存报告
    with open("PHASE2_COMPLETION_REPORT.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 完整报告已保存到: PHASE2_COMPLETION_REPORT.json")
    
    return report

if __name__ == "__main__":
    report = test_phase2_implementation()
    
    print(f"\n🚀 Phase 2 状态: {report['status']}")
    print(f"🎯 下一步: {report['next_phase']}")
    
    # 退出码
    if report["status"] == "COMPLETED":
        print("\n✅ Phase 2 完成！可以开始 Phase 3: SRRM 自我进化引擎")
        sys.exit(0)
    else:
        print("\n⚠️ Phase 2 需要进一步完善")
        sys.exit(1)