"""
Unit tests for Causal Tracing System
"""

import pytest
from datetime import datetime
import asyncio

from apps.backend.src.core.tracing import (
    CausalNode,
    CausalChain,
    LayerType,
    CausalTracer,
    get_tracer,
    ChainValidator,
)


class TestCausalNode:
    def test_node_creation(self):
        node = CausalNode(
            layer=LayerType.L1,
            module="test_module",
            action="test_action",
            data={"key": "value"}
        )
        
        assert node.layer == LayerType.L1
        assert node.module == "test_module"
        assert node.action == "test_action"
        assert node.data["key"] == "value"
        assert node.id is not None
        assert node.parent_id is None
    
    def test_node_serialization(self):
        node = CausalNode(
            layer=LayerType.L2,
            module="memory",
            action="store",
            data={"content": "test"}
        )
        
        node_dict = node.to_dict()
        
        assert node_dict["layer"] == "L2"
        assert node_dict["module"] == "memory"
        assert node_dict["action"] == "store"
        assert node_dict["data"]["content"] == "test"
        
        restored_node = CausalNode.from_dict(node_dict)
        
        assert restored_node.layer == LayerType.L2
        assert restored_node.module == "memory"
        assert restored_node.action == "store"


class TestCausalChain:
    def test_chain_creation(self):
        chain = CausalChain(root_id="test_root")
        
        assert chain.root_id == "test_root"
        assert len(chain.nodes) == 0
    
    def test_add_nodes(self):
        chain = CausalChain(root_id="root")
        
        root = CausalNode(
            id="root",
            layer=LayerType.L1,
            module="test",
            action="init"
        )
        child = CausalNode(
            id="child",
            parent_id="root",
            layer=LayerType.L2,
            module="test",
            action="process"
        )
        
        chain.add_node(root)
        chain.add_node(child)
        
        assert len(chain.nodes) == 2
        assert chain.get_node("root") is not None
        assert chain.get_node("child") is not None
    
    def test_has_layer(self):
        chain = CausalChain(root_id="root")
        
        node1 = CausalNode(layer=LayerType.L1, module="test", action="a")
        node2 = CausalNode(layer=LayerType.L3, module="test", action="b")
        
        chain.add_node(node1)
        chain.add_node(node2)
        
        assert chain.has_layer(LayerType.L1) == True
        assert chain.has_layer(LayerType.L3) == True
        assert chain.has_layer(LayerType.L5) == False
    
    def test_get_children(self):
        chain = CausalChain(root_id="root")
        
        root = CausalNode(id="root", layer=LayerType.L1, module="test", action="init")
        child1 = CausalNode(id="c1", parent_id="root", layer=LayerType.L2, module="test", action="a")
        child2 = CausalNode(id="c2", parent_id="root", layer=LayerType.L2, module="test", action="b")
        
        chain.add_node(root)
        chain.add_node(child1)
        chain.add_node(child2)
        
        children = chain.get_children("root")
        
        assert len(children) == 2
        assert any(c.id == "c1" for c in children)
        assert any(c.id == "c2" for c in children)
    
    def test_path_to_root(self):
        chain = CausalChain(root_id="root")
        
        root = CausalNode(id="root", layer=LayerType.L1, module="test", action="init")
        child = CausalNode(id="child", parent_id="root", layer=LayerType.L2, module="test", action="a")
        grandchild = CausalNode(id="grandchild", parent_id="child", layer=LayerType.L3, module="test", action="b")
        
        chain.add_node(root)
        chain.add_node(child)
        chain.add_node(grandchild)
        
        path = chain.get_path_to_root("grandchild")
        
        assert len(path) == 3
        assert path[0].id == "root"
        assert path[1].id == "child"
        assert path[2].id == "grandchild"


class TestCausalTracer:
    def setup_method(self):
        tracer = get_tracer()
        tracer.clear_chains()
        tracer.enable()
    
    def test_tracer_singleton(self):
        tracer1 = get_tracer()
        tracer2 = get_tracer()
        
        assert tracer1 is tracer2
    
    def test_start_trace(self):
        tracer = get_tracer()
        
        trace_id = tracer.start(
            layer="L1",
            module="test",
            action="test_action",
            data={"test": "value"}
        )
        
        assert trace_id != ""
        assert trace_id in tracer._active_traces
    
    def test_record_data(self):
        tracer = get_tracer()
        
        trace_id = tracer.start(
            layer="L1",
            module="test",
            action="test_action"
        )
        
        tracer.record(trace_id, "key1", "value1")
        tracer.record(trace_id, "key2", 42)
        
        node = tracer._active_traces[trace_id]
        
        assert node.data["key1"] == "value1"
        assert node.data["key2"] == 42
    
    def test_finish_trace(self):
        tracer = get_tracer()
        
        trace_id = tracer.start(
            layer="L1",
            module="test",
            action="test_action"
        )
        
        tracer.finish(trace_id, result="success")
        
        assert trace_id not in tracer._active_traces
        
        chain = tracer.get_chain(trace_id)
        node = chain.get_node(trace_id)
        
        assert node.data["result"] == "success"
    
    def test_parent_child_linking(self):
        tracer = get_tracer()
        
        parent_id = tracer.start(
            layer="L1",
            module="test",
            action="parent"
        )
        
        child_id = tracer.start(
            layer="L2",
            module="test",
            action="child",
            parent_id=parent_id
        )
        
        tracer.finish(parent_id)
        tracer.finish(child_id)
        
        chain = tracer.get_chain(parent_id)
        
        assert chain is not None
        assert len(chain.nodes) == 2
        
        child_node = chain.get_node(child_id)
        
        assert child_node.parent_id == parent_id
    
    def test_enable_disable(self):
        tracer = get_tracer()
        
        tracer.enable()
        assert tracer.is_enabled() == True
        
        trace_id = tracer.start("L1", "test", "action")
        assert trace_id != ""
        
        tracer.disable()
        assert tracer.is_enabled() == False
        
        trace_id = tracer.start("L1", "test", "action2")
        assert trace_id == ""


class TestChainValidator:
    def test_validate_empty_chain(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        
        result = validator.validate_chain(chain)
        
        assert result.valid == False
        assert len(result.errors) > 0
    
    def test_validate_complete_chain(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        
        root = CausalNode(id="root", layer=LayerType.L1, module="test", action="init")
        child = CausalNode(id="child", parent_id="root", layer=LayerType.L2, module="test", action="process")
        
        chain.add_node(root)
        chain.add_node(child)
        
        result = validator.validate_chain(chain)
        
        assert result.valid == True
    
    def test_detect_broken_link(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        
        root = CausalNode(id="root", layer=LayerType.L1, module="test", action="init")
        child = CausalNode(id="child", parent_id="missing", layer=LayerType.L2, module="test", action="process")
        
        chain.add_node(root)
        chain.add_node(child)
        
        result = validator.validate_chain(chain)
        
        assert result.valid == False
        assert any("Broken link" in error for error in result.errors)
    
    def test_layer_coverage(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        
        root = CausalNode(id="root", layer=LayerType.L1, module="test", action="init")
        child = CausalNode(id="child", parent_id="root", layer=LayerType.L2, module="test", action="process")
        
        chain.add_node(root)
        chain.add_node(child)
        
        result = validator.validate_layer_coverage(
            chain,
            [LayerType.L1, LayerType.L2]
        )
        
        assert result.valid == True
        
        result = validator.validate_layer_coverage(
            chain,
            [LayerType.L1, LayerType.L2, LayerType.L6]
        )
        
        assert result.valid == False
    
    def test_get_statistics(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        
        root = CausalNode(id="root", layer=LayerType.L1, module="test", action="init")
        child1 = CausalNode(id="c1", parent_id="root", layer=LayerType.L2, module="test", action="a")
        child2 = CausalNode(id="c2", parent_id="root", layer=LayerType.L3, module="test", action="b")
        
        chain.add_node(root)
        chain.add_node(child1)
        chain.add_node(child2)
        
        stats = validator.get_chain_statistics(chain)
        
        assert stats["total_nodes"] == 3
        assert stats["layer_counts"]["L1"] == 1
        assert stats["layer_counts"]["L2"] == 1
        assert stats["layer_counts"]["L3"] == 1
        assert "L1" in stats["layers_present"]
        assert "L2" in stats["layers_present"]
        assert "L3" in stats["layers_present"]


@pytest.mark.asyncio
async def test_performance_overhead():
    """Test that tracing overhead is minimal"""
    import time
    
    tracer = get_tracer()
    tracer.clear_chains()
    tracer.enable()
    
    iterations = 1000
    
    start = time.time()
    for i in range(iterations):
        trace_id = tracer.start("L1", "test", "action")
        tracer.record(trace_id, "iteration", i)
        tracer.finish(trace_id)
    
    elapsed = time.time() - start
    per_trace = elapsed / iterations
    
    assert per_trace < 0.001
    print(f"Average trace time: {per_trace*1000:.3f}ms")
