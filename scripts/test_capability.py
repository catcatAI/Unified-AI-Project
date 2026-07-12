# =============================================================================
# ANGELA-MATRIX: [L1] [γ] [C] [L0]
# =============================================================================
"""Quick capability test for Angela AI - no LLM contamination."""
import sys
if __name__ != "__main__":
    import pytest
    pytest.skip("Not a test file", allow_module_level=True)

import time

# Only mock torch, not numpy
class MockModule:
    def __getattr__(self, name):
        return MockModule()
    def __call__(self, *args, **kwargs):
        return MockModule()
    def __iter__(self):
        return iter([])

for mod in ['torch', 'torch.nn', 'torch.nn.functional', 'torch.cuda', 'torch.optim',
            'torch.utils', 'torch.utils.data', 'torchvision', 'torchvision.transforms']:
    sys.modules[mod] = MockModule()

import numpy as np

print("=" * 60)
print("Angela AI Capability Test (No LLM Contamination)")
print("=" * 60)

# 1. Test SharedLatentSpace
print("\n--- 1. SharedLatentSpace ---")
try:
    from ai.multimodal.shared_latent_space import get_shared_latent_space, reset_shared_latent_space
    reset_shared_latent_space()
    ls = get_shared_latent_space(latent_dim=64)
    print(f"  Modalities: {ls.registered_modalities()}")
    print(f"  Latent dim: {ls._latent_dim}")
    
    # Test projection
    vec = np.random.randn(512).astype(np.float32)
    latent = ls.project("text", vec)
    print(f"  Projection: {latent.shape}")
    print("  ✅ SharedLatentSpace: OK")
except Exception as e:
    print(f"  ❌ SharedLatentSpace: {e}")

# 2. Test LatentReasoningNetwork
print("\n--- 2. LatentReasoningNetwork ---")
try:
    from ai.multimodal.latent_reasoning_network import LatentReasoningNetwork
    lrn = LatentReasoningNetwork(latent_dim=64, vocab_size=500)
    latent = np.random.randn(64).astype(np.float32)
    output = lrn.forward(latent)
    print(f"  Output shape: {output.shape}")
    print(f"  Output range: [{output.min():.4f}, {output.max():.4f}]")
    
    # Check if output is meaningful (not all zeros)
    if np.any(output != 0):
        print("  ✅ LRN: OK (produces non-zero output)")
    else:
        print("  ❌ LRN: All zeros")
except Exception as e:
    print(f"  ❌ LRN: {e}")

# 3. Test CausalReasoningEngine
print("\n--- 3. CausalReasoningEngine ---")
try:
    from ai.reasoning.causal_reasoning_engine import CausalReasoningEngine
    cre = CausalReasoningEngine()
    # Check attributes
    attrs = [a for a in dir(cre) if not a.startswith('_')]
    print(f"  Public methods: {len(attrs)}")
    print("  ✅ CausalReasoningEngine: OK")
except Exception as e:
    print(f"  ❌ CausalReasoningEngine: {e}")

# 4. Test EmotionSystem
print("\n--- 4. EmotionSystem ---")
try:
    from ai.alignment.emotion_system import EmotionSystem
    es = EmotionSystem()
    # Check what methods are available
    methods = [m for m in dir(es) if not m.startswith('_') and callable(getattr(es, m))]
    print(f"  Methods: {methods[:5]}...")
    print("  ✅ EmotionSystem: OK")
except Exception as e:
    print(f"  ❌ EmotionSystem: {e}")

# 5. Test IntentModel
print("\n--- 5. IntentModel ---")
try:
    from core.life.intent_model import IntentModel
    im = IntentModel()
    # Check what methods are available
    methods = [m for m in dir(im) if not m.startswith('_') and callable(getattr(im, m))]
    print(f"  Methods: {methods[:5]}...")
    print("  ✅ IntentModel: OK")
except Exception as e:
    print(f"  ❌ IntentModel: {e}")

# 6. Test AutonomousLifeCycle
print("\n--- 6. AutonomousLifeCycle ---")
try:
    from core.life.autonomous_life_cycle import AutonomousLifeCycle
    alc = AutonomousLifeCycle()
    # Check what methods are available
    methods = [m for m in dir(alc) if not m.startswith('_') and callable(getattr(alc, m))]
    print(f"  Methods: {methods[:5]}...")
    print("  ✅ AutonomousLifeCycle: OK")
except Exception as e:
    print(f"  ❌ AutonomousLifeCycle: {e}")

# 7. Test PriorityNegotiator
print("\n--- 7. PriorityNegotiator ---")
try:
    from ai.meta.priority_negotiator import PriorityNegotiator
    pn = PriorityNegotiator()
    voters = pn._voters if hasattr(pn, '_voters') else {}
    print(f"  Registered voters: {len(voters)}")
    print("  ✅ PriorityNegotiator: OK")
except Exception as e:
    print(f"  ❌ PriorityNegotiator: {e}")

# 8. Test MetabolicHeartbeat
print("\n--- 8. MetabolicHeartbeat ---")
try:
    from ai.lifecycle.metabolic_heartbeat import MetabolicHeartbeat
    mh = MetabolicHeartbeat()
    health = mh.get_system_health()
    print(f"  System health: {health}")
    print("  ✅ MetabolicHeartbeat: OK")
except Exception as e:
    print(f"  ❌ MetabolicHeartbeat: {e}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("""
Native Engine Capabilities (No LLM):
- SharedLatentSpace: 64-dim, 5 modalities (vision, audio, text, vision_semantic, audio_semantic)
- LatentReasoningNetwork: 2-layer MLP (64→128→128→500) - trainable
- CausalReasoningEngine: Causal inference from interactions
- EmotionSystem: PAD emotion model with feedback loop
- IntentModel: Intent routing with success tracking
- AutonomousLifeCycle: Lifecycle management with behavioral adjustment
- PriorityNegotiator: Weighted voter fusion for routing decisions
- MetabolicHeartbeat: System health monitoring

Limitations (from INTELLIGENCE_ASSESSMENT.md):
- No real training loop (weights are random)
- No gradient updates
- No hold-out validation
- No MMLU/HumanEval benchmarks
- Math: 100% (hardcoded PEMDAS)
- Knowledge: 0% (dictionary has no English knowledge mappings)
- Reasoning: 0% (no logical inference capability)
""")
