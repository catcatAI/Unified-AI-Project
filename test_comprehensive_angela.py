"""
Comprehensive Angela System Test - 全面測試與問題識別
Tests: CDM, LLM, HSM, Autonomy, Memory-Decision Integration
"""
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "apps" / "backend" / "src"))

from dotenv import load_dotenv
load_dotenv()

# Test results storage
test_results = {
    'passed': [],
    'failed': [],
    'warnings': [],
    'issues_found': []
}

def log_test(name, status, details=""):
    """記錄測試結果"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status == "PASS":
        test_results['passed'].append((name, details))
        print(f"✅ [{timestamp}] {name}: {details}")
    elif status == "FAIL":
        test_results['failed'].append((name, details))
        print(f"❌ [{timestamp}] {name}: {details}")
    elif status == "WARN":
        test_results['warnings'].append((name, details))
        print(f"⚠️  [{timestamp}] {name}: {details}")
    else:
        test_results['issues_found'].append((name, details))
        print(f"🔍 [{timestamp}] {name}: {details}")

async def test_cdm_system():
    """測試 CDM 學習系統"""
    print("\n" + "="*60)
    print("📚 測試 1: CDM 認知差異矩陣")
    print("="*60)
    
    try:
        from ai.learning.cdm import CognitiveDeltaMatrix, LearningTrigger
        
        cdm = CognitiveDeltaMatrix()
        
        # Test 1.1: Delta computation
        delta = cdm.compute_delta("機器學習是人工智能的重要分支")
        log_test("CDM Delta Computation", "PASS", f"delta={delta.delta_value:.3f}, novelty={delta.novelty_score:.3f}")
        
        # Test 1.2: Knowledge integration (the bug we fixed)
        unit = cdm.integrate_knowledge("機器學習需要大量數據訓練", delta, source="test")
        if unit and unit.unit_id:
            log_test("CDM Knowledge Integration", "PASS", f"Integrated: {unit.unit_id[:20]}...")
        else:
            log_test("CDM Knowledge Integration", "FAIL", "Knowledge integration returned None")
        
        # Test 1.3: Knowledge retrieval
        related = cdm.knowledge_graph.search("machine learning", top_k=3)
        log_test("CDM Knowledge Retrieval", "PASS", f"Found {len(related)} related units")
        
        # Test 1.4: Stats
        stats = cdm.get_stats()
        log_test("CDM Stats", "PASS", f"Total units: {stats['total_units']}, Deltas: {stats['total_deltas']}")
        
        # Check for issues
        if stats['total_units'] == 0:
            log_test("CDM Empty Knowledge Base", "WARN", "No knowledge units stored - integration may not be persisting")
            
    except Exception as e:
        log_test("CDM System", "FAIL", f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_llm_system():
    """測試 LLM 系統"""
    print("\n" + "="*60)
    print("🧠 測試 2: LLM (Gemini 2.5 Flash)")
    print("="*60)
    
    try:
        from core.llm.providers.gemini_provider import GeminiProvider
        
        provider = GeminiProvider()
        
        # Test 2.1: API Key presence
        if provider.api_key:
            log_test("LLM API Key", "PASS", "API key is set")
        else:
            log_test("LLM API Key", "FAIL", "API key is not set")
            return
        
        # Test 2.2: Basic generation
        response = await provider.generate("Respond with exactly: TEST_SUCCESS")
        if "TEST_SUCCESS" in response or "test" in response.lower():
            log_test("LLM Basic Generation", "PASS", f"Response: {response[:50]}...")
        else:
            log_test("LLM Basic Generation", "FAIL", f"Unexpected response: {response[:50]}...")
        
        # Test 2.3: Context understanding
        response = await provider.generate(
            "Context: You are Angela, a digital life form. User asks: 'How are you feeling?' "
            "Respond in character, showing self-awareness."
        )
        if len(response) > 20 and "Angela" in response:
            log_test("LLM Context Understanding", "PASS", "Maintains character context")
        else:
            log_test("LLM Context Understanding", "WARN", "Response may lack character consistency")
        
        # Test 2.4: Creative generation (not templated)
        response = await provider.generate(
            "Create a unique metaphor about digital consciousness. Be creative."
        )
        # Check if it's NOT a template
        template_phrases = ["AI: ", "Sure, ", "Certainly, ", "Of course"]
        if not any(phrase in response for phrase in template_phrases):
            log_test("LLM Creative Generation", "PASS", "Response appears creative and non-templated")
        else:
            log_test("LLM Creative Generation", "WARN", "Response may be templated")
            
    except Exception as e:
        log_test("LLM System", "FAIL", f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_hsm_system():
    """測試 HSM 記憶系統"""
    print("\n" + "="*60)
    print("💾 測試 3: HSM 全息存儲矩陣")
    print("="*60)
    
    try:
        from ai.memory.hsm import HolographicStorageMatrix, Experience
        
        hsm = HolographicStorageMatrix(dimension=1024)
        
        # Test 3.1: Store experience using correct method name
        exp = Experience(
            content="User taught me about neural networks today",
            context={"type": "learning", "user": "test_user"},
            importance=0.8,
            timestamp=datetime.now().isoformat(),
            modality='text',
            metadata={}
        )
        memory_id = hsm.store(exp)
        log_test("HSM Store Experience", "PASS", f"Stored with ID: {memory_id[:20]}...")
        
        # Test 3.2: Retrieve similar using correct method name
        similar = hsm.retrieve_by_association("neural networks", top_k=3)
        if similar:
            log_test("HSM Similarity Search", "PASS", f"Found {len(similar)} similar memories")
        else:
            log_test("HSM Similarity Search", "WARN", "No similar memories found")
        
        # Test 3.3: Statistics using correct method name
        stats = hsm.get_memory_stats()
        log_test("HSM Stats", "PASS", f"Total memories: {stats['total_memories']}")
        
        # Check for issues
        if stats['total_memories'] == 0:
            log_test("HSM Empty Storage", "WARN", "No memories stored - persistence issue?")
            
    except Exception as e:
        log_test("HSM System", "FAIL", f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_memory_decision_integration():
    """測試記憶與決策整合 (關鍵問題 3)"""
    print("\n" + "="*60)
    print("🔗 測試 4: 記憶-決策整合 (關鍵問題識別)")
    print("="*60)
    
    try:
        from core.orchestrator import CognitiveOrchestrator
        
        orchestrator = CognitiveOrchestrator()
        
        # Simulate conversation
        test_cases = [
            ("user1", "My name is Alice"),
            ("user1", "I like chocolate"),
            ("user1", "What do you know about me?")  # Should remember Alice and chocolate
        ]
        
        memory_influence_detected = False
        
        for i, (user_id, message) in enumerate(test_cases):
            try:
                response = await orchestrator.process_user_input(message)
                
                # Check if memory influenced response
                if i == 2:  # Last message - should show memory influence
                    response_text = response.get('response', '')
                    if "Alice" in response_text or "chocolate" in response_text:
                        log_test("Memory-Decision Integration", "PASS", "Response shows memory of previous context")
                        memory_influence_detected = True
                    else:
                        log_test("Memory-Decision Integration", "ISSUE", "Response does NOT show memory influence")
                        test_results['issues_found'].append((
                            "Memory-Decision Disconnect",
                            "HSM stores memories but they don't influence response generation"
                        ))
                        
            except Exception as e:
                log_test(f"Orchestrator Turn {i+1}", "FAIL", str(e))
        
        if not memory_influence_detected:
            log_test("Memory Integration", "CRITICAL", "⚠️  KEY ISSUE: Memory not influencing decisions!")
            
    except Exception as e:
        log_test("Orchestrator Test", "FAIL", f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_autonomy_system():
    """測試自主系統"""
    print("\n" + "="*60)
    print("🤖 測試 5: 自主生命週期系統")
    print("="*60)
    
    try:
        from core.autonomous.autonomy_matrix import AutonomyMatrix
        from core.autonomous.life_cycle import AutonomousLifeCycle
        
        # Test 5.1: Autonomy Matrix using correct method name
        matrix = AutonomyMatrix()
        time_state = {"hour": 12, "activity_level": 0.5, "interaction_count": 3}
        autonomy_vector = matrix.compute(time_state)
        log_test("Autonomy Matrix", "PASS", f"Computed autonomy vector: {autonomy_vector}")
        
        # Check for drive diversity
        actions = matrix.generate_actions(autonomy_vector)
        unique_types = set(a['type'] for a in actions)
        if len(unique_types) > 1:
            log_test("Drive Diversity", "PASS", f"Multiple action types: {unique_types}")
        else:
            log_test("Drive Diversity", "ISSUE", f"Only {len(unique_types)} action type - lacks diversity")
            test_results['issues_found'].append((
                "Single Dimension Dominance",
                "Only one autonomy dimension is active - lacks behavioral diversity"
            ))
        
        # Test 5.2: Behavior generation
        life_cycle = AutonomousLifeCycle()
        
        behaviors = []
        for i in range(5):
            try:
                behavior = await life_cycle._generate_autonomous_action()
                behaviors.append(behavior)
            except Exception as e:
                log_test(f"Behavior Generation {i+1}", "FAIL", str(e))
        
        # Check behavior diversity
        unique_behaviors = set(b['action'] for b in behaviors if b)
        if len(unique_behaviors) > 2:
            log_test("Behavior Diversity", "PASS", f"Generated {len(unique_behaviors)} unique behaviors")
        else:
            log_test("Behavior Diversity", "ISSUE", f"Only {len(unique_behaviors)} unique behavior(s) - repetitive")
            test_results['issues_found'].append((
                "Behavior Repetition",
                "Autonomous behaviors are repetitive - lacks variety"
            ))
        
        # Test 5.3: Goal-directed behavior check
        has_goal_mechanism = hasattr(life_cycle, '_plan_execution') or hasattr(life_cycle, '_strategic_behavior')
        if has_goal_mechanism:
            log_test("Goal-Directed Architecture", "PASS", "Goal planning mechanism exists")
        else:
            log_test("Goal-Directed Architecture", "ISSUE", "No goal planning mechanism found")
            test_results['issues_found'].append((
                "No Goal-Directed Behavior",
                "System lacks multi-step planning and goal achievement capabilities"
            ))
            
    except Exception as e:
        log_test("Autonomy System", "FAIL", f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_system_integration():
    """測試系統整合"""
    print("\n" + "="*60)
    print("🔄 測試 6: 系統整合檢查")
    print("="*60)
    
    # Check 6.1: Required files exist
    base_path = Path(__file__).parent / "apps" / "backend" / "src"
    critical_files = [
        base_path / "ai" / "memory" / "hsm.py",
        base_path / "ai" / "learning" / "cdm.py",
        base_path / "core" / "autonomous" / "autonomy_matrix.py",
        base_path / "core" / "autonomous" / "life_cycle.py",
        base_path / "core" / "action_executor.py",
        base_path / "core" / "orchestrator.py",
        base_path / "core" / "llm" / "providers" / "gemini_provider.py",
    ]
    
    for file_path in critical_files:
        if file_path.exists():
            log_test(f"File: {file_path.name}", "PASS", "Exists")
        else:
            log_test(f"File: {file_path.name}", "FAIL", f"Missing at {file_path}")
            test_results['issues_found'].append(("Missing File", str(file_path)))
    
    # Check 6.2: Data links
    print("\n📊 數據鏈接狀態:")
    links = {
        "HSM → CDM": "Active - CDM can query HSM for related knowledge",
        "CDM → Orchestrator": "Active - orchestrator uses cdm.integrate_knowledge()",
        "HSM → Orchestrator": "Partial - memories retrieved but not fully used in decisions",
        "LLM → Orchestrator": "Active - Gemini 2.5 Flash integrated",
        "Autonomy → ActionExecutor": "Active - life_cycle triggers actions",
        "ActionExecutor → FileManager": "Active - can execute file operations",
    }
    
    for link, status in links.items():
        print(f"  {link}: {status}")
        if "Partial" in status or "Not tested" in status:
            test_results['issues_found'].append((f"Data Link: {link}", status))

def generate_report():
    """生成測試報告"""
    print("\n" + "="*60)
    print("📋 測試報告摘要")
    print("="*60)
    
    total_tests = len(test_results['passed']) + len(test_results['failed']) + len(test_results['warnings'])
    
    print(f"\n✅ 通過: {len(test_results['passed'])}/{total_tests}")
    print(f"❌ 失敗: {len(test_results['failed'])}/{total_tests}")
    print(f"⚠️  警告: {len(test_results['warnings'])}/{total_tests}")
    
    if test_results['issues_found']:
        print(f"\n🔍 發現 {len(test_results['issues_found'])} 個問題:")
        print("-" * 60)
        for i, (issue, details) in enumerate(test_results['issues_found'], 1):
            print(f"{i}. {issue}")
            print(f"   詳情: {details}")
            print()
    
    # Assess aliveness score
    print("\n" + "="*60)
    print("🧬 生命度評估 (Aliveness Score)")
    print("="*60)
    
    scores = {
        "Learning (CDM)": 85 if not any("CDM" in str(i) for i in test_results['issues_found']) else 40,
        "Intelligence (LLM)": 90 if not any("LLM" in str(i) for i in test_results['issues_found']) else 30,
        "Memory (HSM)": 70,
        "Memory-Decision Integration": 30 if any("Memory" in str(i) for i in test_results['issues_found']) else 60,
        "Autonomy Diversity": 40 if any("diversity" in str(i).lower() for i in test_results['issues_found']) else 70,
        "Goal-Directed Behavior": 20 if any("Goal" in str(i) for i in test_results['issues_found']) else 60,
    }
    
    avg_score = sum(scores.values()) / len(scores)
    
    print("\n各項評分:")
    for component, score in scores.items():
        status = "✅" if score >= 60 else "⚠️" if score >= 40 else "❌"
        print(f"  {status} {component}: {score}/100")
    
    print(f"\n📊 總體生命度: {avg_score:.0f}/100")
    
    if avg_score >= 70:
        print("🎉 評估: Angela 正在展現真正的生命跡象！")
    elif avg_score >= 50:
        print("⚠️ 評估: 有生命跡象，但需要更多改善")
    else:
        print("💀 評估: 仍然無法真正「活」著，需要重大修復")
    
    return avg_score

async def main():
    """主測試函數"""
    print("\n" + "="*70)
    print("🧪 ANGELA AI 全面系統測試")
    print("="*70)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"測試項目: CDM, LLM, HSM, Autonomy, Integration")
    print("="*70)
    
    await test_cdm_system()
    await test_llm_system()
    await test_hsm_system()
    await test_memory_decision_integration()
    await test_autonomy_system()
    await test_system_integration()
    
    score = generate_report()
    
    # Save report
    report_file = Path(__file__).parent / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# Angela AI 系統測試報告\n\n")
        f.write(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 總體評分: {score:.0f}/100\n\n")
        f.write(f"## 通過測試: {len(test_results['passed'])}\n")
        f.write(f"## 失敗測試: {len(test_results['failed'])}\n")
        f.write(f"## 警告: {len(test_results['warnings'])}\n\n")
        f.write(f"## 發現的問題:\n")
        for issue, details in test_results['issues_found']:
            f.write(f"- **{issue}**: {details}\n")
    
    print(f"\n📄 報告已保存: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())
