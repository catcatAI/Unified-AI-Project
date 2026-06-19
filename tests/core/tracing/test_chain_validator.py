import pytest
from datetime import datetime
from apps.backend.src.core.tracing.causal_chain import CausalChain, CausalNode, LayerType
from apps.backend.src.core.tracing.chain_validator import ChainValidator, ValidationResult


class TestValidationResult:
    def test_bool_valid(self):
        assert bool(ValidationResult(valid=True, errors=[], warnings=[])) is True

    def test_bool_invalid(self):
        assert bool(ValidationResult(valid=False, errors=["err"], warnings=[])) is False


class TestChainValidator:
    def test_validate_empty_chain(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        result = validator.validate_chain(chain)
        assert result.valid is False
        assert "empty" in result.errors[0].lower()

    def test_validate_valid_chain(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        chain.add_node(CausalNode(id="root", layer=LayerType.L1, module="m", action="start"))
        chain.add_node(CausalNode(id="n1", parent_id="root", layer=LayerType.L2, module="m", action="process"))
        result = validator.validate_chain(chain)
        assert result.valid is True

    def test_broken_link_detected(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        chain.add_node(CausalNode(id="root", layer=LayerType.L1, module="m", action="start"))
        chain.add_node(CausalNode(id="orphan", parent_id="nonexistent", module="m", action="fail"))
        result = validator.validate_chain(chain)
        assert result.valid is False
        assert any("broken" in e.lower() for e in result.errors)

    def test_timestamp_violation(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        now = datetime.now()
        chain.add_node(CausalNode(
            id="root", layer=LayerType.L1, module="m", action="start",
            timestamp=now,
        ))
        chain.add_node(CausalNode(
            id="child", parent_id="root", layer=LayerType.L2, module="m", action="process",
            timestamp=now.replace(year=now.year - 1),
        ))
        result = validator.validate_chain(chain)
        assert result.valid is False
        assert any("timestamp" in e.lower() for e in result.errors)

    def test_root_with_parent_is_invalid(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        chain.add_node(CausalNode(id="root", parent_id="someone", module="m", action="start"))
        chain.add_node(CausalNode(id="n1", parent_id="root", module="m", action="process"))
        result = validator.validate_chain(chain)
        assert result.valid is False
        assert any("parent" in e.lower() for e in result.errors)

    def test_orphaned_node_detected(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        chain.add_node(CausalNode(id="root", module="m", action="start"))
        chain.add_node(CausalNode(id="orphan", module="m", action="no_parent"))
        result = validator.validate_chain(chain)
        assert result.valid is False
        assert any("orphan" in e.lower() for e in result.errors)

    def test_validate_layer_coverage_all_present(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        chain.add_node(CausalNode(id="root", layer=LayerType.L1, module="m", action="start"))
        chain.add_node(CausalNode(id="n1", parent_id="root", layer=LayerType.L3, module="m", action="process"))
        result = validator.validate_layer_coverage(chain, [LayerType.L1, LayerType.L3])
        assert result.valid is True

    def test_validate_layer_coverage_missing(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        chain.add_node(CausalNode(id="root", layer=LayerType.L1, module="m", action="start"))
        result = validator.validate_layer_coverage(chain, [LayerType.L1, LayerType.L5])
        assert result.valid is False

    def test_get_chain_statistics(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        chain.add_node(CausalNode(id="root", layer=LayerType.L1, module="m", action="start"))
        chain.add_node(CausalNode(id="n1", parent_id="root", layer=LayerType.L2, module="m", action="process"))
        stats = validator.get_chain_statistics(chain)
        assert stats["total_nodes"] == 2
        assert "layer_counts" in stats
        assert "execution_time" in stats
        assert "layers_present" in stats

    def test_unusual_layer_transition_warning(self):
        validator = ChainValidator()
        chain = CausalChain(root_id="root")
        chain.add_node(CausalNode(id="root", layer=LayerType.L5, module="m", action="start"))
        chain.add_node(CausalNode(
            id="n1", parent_id="root", layer=LayerType.L1,
            module="m", action="backwards",
        ))
        result = validator.validate_chain(chain)
        assert result.valid is True
        assert len(result.warnings) > 0
        assert any("backward" in w.lower() for w in result.warnings)
