"""
Long-term drift test for Endocrine System.
Ensures that hormone levels correctly return to steady state (base_level) 
over a large number of cycles (10,000 ticks).
"""
import asyncio
import math
import sys
from pathlib import Path

# Add project root (apps/backend) to sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.autonomous.endocrine_system import EndocrineSystem, HormoneType


async def test_long_term_drift():
    print("🚀 [Behavioral Test] Starting Long-term Drift Analysis...")
    system = EndocrineSystem()
    
    # 1. Perturb the system away from steady state
    print("Perturbing all hormones to max levels...")
    for ht in HormoneType:
        await system.adjust_hormone(ht, 100.0)
        
    initial_hormones = system.get_all_hormone_levels()
    
    # 2. Simulate 100,000 updates of 1 minute each (Total ~1666 hours / ~69 days)
    print("Simulating 100,000 minute-level ticks...")
    for i in range(100000):
        await system.advance_time(60.0) # 60 seconds = 1 min
        
        if i % 20000 == 0:
            avg_drift = sum(abs(system.get_hormone_level(ht) - system.hormones[ht].base_level) for ht in HormoneType) / 12
            print(f"   Tick {i}: Average Drift from Base={avg_drift:.4f}")

    # 3. Final Convergence Check
    print("\nVerifying convergence to Steady State (Base Levels)...")
    for ht in HormoneType:
        current = system.get_hormone_level(ht)
        base = system.hormones[ht].base_level
        drift = abs(current - base)
        print(f"   {ht.en_name}: Final={current:.4f}, Base={base:.1f}, Drift={drift:.6f}")
        
        # Long-lived hormones like Thyroxine (7d half-life) need many days to converge
        # After 70 days (~10 half-lives), 40.0 * (0.5^10) = 40 * 0.00097 \approx 0.039
        # So we use 0.05 as a safe threshold for 100k ticks
        assert drift < 0.05, f"Convergence failure for {ht.en_name}. Drift too high: {drift}"
        
    print("\n✅ Long-term drift test passed! System is biologically stable.")

if __name__ == "__main__":
    asyncio.run(test_long_term_drift())
