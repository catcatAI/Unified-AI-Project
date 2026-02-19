"""
Integration tests for end-to-end causal tracing through L1-L6 layers
"""

import pytest
import asyncio

from apps.backend.src.core.tracing import (
    get_tracer,
    ChainValidator,
    LayerType,
)
from apps.backend.src.core.autonomous.endocrine_system import (
    EndocrineSystem,
    HormoneType,
)
from apps.backend.src.core.autonomous.cyber_identity import (
    CyberIdentity,
    IdentityAspect,
)


@pytest.mark.asyncio
class TestEndToEndTracing:
    async def test_l1_hormone_tracing(self):
        """Test L1 endocrine system tracing"""
        tracer = get_tracer()
        tracer.clear_chains()
        tracer.enable()
        
        endocrine = EndocrineSystem()
        await endocrine.initialize()
        
        await endocrine.adjust_hormone(HormoneType.DOPAMINE, 10.0)
        
        await asyncio.sleep(0.1)
        
        chains = tracer.get_all_chains()
        
        assert len(chains) > 0
        
        chain = chains[0]
        
        assert chain.has_layer(LayerType.L1)
        
        l1_nodes = chain.get_layer_nodes(LayerType.L1)
        
        assert len(l1_nodes) > 0
        
        node = l1_nodes[0]
        
        assert node.module == "endocrine_system"
        assert node.action == "adjust_hormone"
        assert node.data["hormone"] == "Dopamine"
        
        await endocrine.shutdown()
    
    async def test_l1_emotional_response_tracing(self):
        """Test L1 emotional response tracing with hormone cascades"""
        tracer = get_tracer()
        tracer.clear_chains()
        tracer.enable()
        
        endocrine = EndocrineSystem()
        await endocrine.initialize()
        
        await endocrine.trigger_emotional_response("joy", 0.8)
        
        await asyncio.sleep(0.1)
        
        chains = tracer.get_all_chains()
        
        assert len(chains) > 0
        
        root_chain = chains[0]
        
        root_node = root_chain.get_node(root_chain.root_id)
        
        assert root_node.action == "trigger_emotional_response"
        assert root_node.data["emotion"] == "joy"
        assert root_node.data["intensity"] == 0.8
        
        children = root_chain.get_children(root_chain.root_id)
        
        assert len(children) > 0
        
        await endocrine.shutdown()
    
    async def test_l3_identity_growth_tracing(self):
        """Test L3 cyber identity tracing"""
        tracer = get_tracer()
        tracer.clear_chains()
        tracer.enable()
        
        identity = CyberIdentity()
        await identity.initialize()
        
        identity.record_growth(
            IdentityAspect.SELF_AWARENESS,
            0.7,
            milestone="Reached 70% self-awareness"
        )
        
        await asyncio.sleep(0.1)
        
        chains = tracer.get_all_chains()
        
        assert len(chains) > 0
        
        chain = chains[0]
        
        assert chain.has_layer(LayerType.L3)
        
        l3_nodes = chain.get_layer_nodes(LayerType.L3)
        
        assert len(l3_nodes) > 0
        
        node = l3_nodes[0]
        
        assert node.module == "cyber_identity"
        assert node.action == "record_growth"
        assert node.data["aspect"] == "SELF_AWARENESS"
        assert node.data["new_level"] == 0.7
        
        await identity.shutdown()
    
    async def test_chain_validation(self):
        """Test chain validation after tracing operations"""
        tracer = get_tracer()
        tracer.clear_chains()
        tracer.enable()
        
        endocrine = EndocrineSystem()
        await endocrine.initialize()
        
        await endocrine.trigger_emotional_response("joy", 0.8)
        
        await asyncio.sleep(0.1)
        
        chains = tracer.get_all_chains()
        
        assert len(chains) > 0
        
        validator = ChainValidator()
        
        for chain in chains:
            result = validator.validate_chain(chain)
            
            if not result.valid:
                print(f"Chain validation errors: {result.errors}")
                print(f"Chain validation warnings: {result.warnings}")
            
            assert result.valid == True
        
        await endocrine.shutdown()
    
    async def test_trace_performance(self):
        """Test that tracing overhead is minimal in real usage"""
        import time
        
        tracer = get_tracer()
        tracer.clear_chains()
        
        endocrine = EndocrineSystem()
        await endocrine.initialize()
        
        tracer.disable()
        start_disabled = time.time()
        for i in range(100):
            await endocrine.adjust_hormone(HormoneType.DOPAMINE, 1.0)
        time_disabled = time.time() - start_disabled
        
        await asyncio.sleep(0.5)
        
        tracer.enable()
        start_enabled = time.time()
        for i in range(100):
            await endocrine.adjust_hormone(HormoneType.DOPAMINE, 1.0)
        time_enabled = time.time() - start_enabled
        
        overhead_ratio = time_enabled / time_disabled if time_disabled > 0 else 1.0
        
        print(f"Time disabled: {time_disabled:.3f}s")
        print(f"Time enabled: {time_enabled:.3f}s")
        print(f"Overhead ratio: {overhead_ratio:.2f}x")
        
        assert overhead_ratio < 10.0
        
        await endocrine.shutdown()
    
    async def test_chain_statistics(self):
        """Test chain statistics calculation"""
        tracer = get_tracer()
        tracer.clear_chains()
        tracer.enable()
        
        endocrine = EndocrineSystem()
        await endocrine.initialize()
        
        await endocrine.trigger_emotional_response("joy", 0.8)
        
        await asyncio.sleep(0.1)
        
        chains = tracer.get_all_chains()
        
        assert len(chains) > 0
        
        validator = ChainValidator()
        
        for chain in chains:
            stats = validator.get_chain_statistics(chain)
            
            assert "total_nodes" in stats
            assert "layer_counts" in stats
            assert "execution_time" in stats
            assert stats["total_nodes"] > 0
            
            print(f"Chain statistics: {stats}")
        
        await endocrine.shutdown()
