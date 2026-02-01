"""
Matrix-Only Mode Test Script
Tests Angela's ability to operate without LLM
"""

import sys
import os

# Add the project root and backend src to path
project_root = r"D:\Projects\Unified-AI-Project"
backend_src = os.path.join(project_root, "apps", "backend", "src")

sys.path.insert(0, project_root)
sys.path.insert(0, backend_src)

# Now we can do absolute imports
from core.autonomous.enhanced_life_cycle import EnhancedAutonomousLifeCycle
import asyncio
import time

async def test_matrix_only_mode():
    """Test matrix-only operation for 30 seconds"""
    print("\n" + "="*70)
    print("🧪 Testing Matrix-Only Mode (No LLM)")
    print("="*70)
    
    # Initialize with model enhancement DISABLED
    lifecycle = EnhancedAutonomousLifeCycle(use_model_enhancement=False)
    
    print("\n📊 Configuration:")
    print(f"   Mode: Enhanced (Matrix-Driven)")
    print(f"   Model Enhancement: DISABLED")
    print(f"   Pure Matrix Expression: ENABLED")
    
    # Start the lifecycle
    await lifecycle.start()
    
    print("\n⏱️  Running for 30 seconds...")
    print("   (Matrix will generate decisions and expressions independently)\n")
    
    # Let it run
    await asyncio.sleep(30)
    
    # Collect stats
    stats = lifecycle.get_stats()
    analysis = lifecycle.get_decision_analysis()
    
    # Stop
    await lifecycle.stop()
    
    # Report results
    print("\n" + "="*70)
    print("📈 EXECUTION STATISTICS")
    print("="*70)
    print(f"\nTotal Executions: {stats['total_executions']}")
    print(f"Successful: {stats['successful_executions']}")
    print(f"Success Rate: {stats['success_rate']:.1%}")
    print(f"\n🎯 Matrix Dominance:")
    print(f"   Matrix-Only Success: {stats['matrix_only_success']}")
    print(f"   Matrix Dominance Rate: {stats['matrix_dominance_rate']:.1%}")
    print(f"   Model Enhanced: {stats['model_enhanced_count']} (should be 0)")
    
    print("\n" + "="*70)
    print("🔍 DECISION ANALYSIS")
    print("="*70)
    print(f"\nTotal Decisions: {analysis.get('total_decisions', 0)}")
    print(f"Dominant Drive: {analysis.get('dominant_drive', 'N/A')}")
    print(f"Average Intensity: {analysis.get('average_intensity', 'N/A')}")
    print(f"Model Dependency: {analysis.get('model_dependency_rate', 'N/A')}")
    
    print(f"\n📊 Drive Distribution:")
    for drive, count in analysis.get('drive_distribution', {}).items():
        print(f"   {drive}: {count}")
    
    print(f"\n📊 Action Categories:")
    for cat, count in analysis.get('category_distribution', {}).items():
        print(f"   {cat}: {count}")
    
    print("\n📜 Recent Decisions (Last 5):")
    for decision in stats.get('recent_decisions', []):
        print(f"   [{decision['drive']}] {decision['category']} "
              f"(intensity: {decision['intensity']}, success: {decision['success']})")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)
    
    # Validate results
    success = True
    issues = []
    
    if stats['model_enhanced_count'] != 0:
        success = False
        issues.append("❌ Model was called when it should be disabled")
    
    if stats['matrix_dominance_rate'] < 0.9:
        success = False
        issues.append(f"❌ Matrix dominance too low: {stats['matrix_dominance_rate']:.1%}")
    
    if stats['total_executions'] == 0:
        success = False
        issues.append("❌ No executions occurred (all drives below threshold?)")
    
    if success:
        print("\n🎉 SUCCESS: Matrix-only mode operates correctly!")
        print(f"   - {stats['matrix_only_success']} behaviors executed without LLM")
        print(f"   - {analysis.get('total_decisions', 0)} autonomous decisions made")
        print(f"   - 0% dependency on external model")
    else:
        print("\n⚠️  ISSUES DETECTED:")
        for issue in issues:
            print(f"   {issue}")
    
    return success, stats, analysis

if __name__ == "__main__":
    success, stats, analysis = asyncio.run(test_matrix_only_mode())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
