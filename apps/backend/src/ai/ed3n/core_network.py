# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from .dictionary_layer import DictionaryLayer

from core.system.config.magic_numbers import (
    behavior_threshold,
    learning_rate,
    limit_value,
    threshold_value,
)

from .relation_classifier import RelationClassifier, RelationType

logger = logging.getLogger(__name__)


class Neuron:
    def __init__(
        self,
        key: str,
        activation: float = 0.0,
        threshold: float = threshold_value("ai.core_network.neuron_threshold", 0.3),
        connections: Optional[Dict[str, float]] = None,
        group_type: str = "",
    ):
        self.key = key
        self.activation = min(max(activation, 0.0), 1.0)
        self.threshold = threshold
        self.connections = connections or {}
        self.group_type = group_type

    def __repr__(self) -> str:
        return f"Neuron(key={self.key!r}, activation={self.activation:.2f}, group={self.group_type!r})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "activation": self.activation,
            "threshold": self.threshold,
            "connections": dict(self.connections),
            "group_type": self.group_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Neuron":
        return cls(
            key=data["key"],
            activation=data.get("activation", 0.0),
            threshold=data.get("threshold", 0.3),
            connections=data.get("connections", {}),
            group_type=data.get("group_type", ""),
        )


class RelationGroup:
    def __init__(
        self,
        group_type: str,
        neurons: Optional[Dict[str, Neuron]] = None,
        activation_pattern: Optional[Callable[..., None]] = None,
    ):
        self.group_type = group_type
        self.neurons = neurons or {}
        self.activation_pattern = activation_pattern or self._default_activation_pattern

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_type": self.group_type,
            "neurons": {k: n.to_dict() for k, n in self.neurons.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RelationGroup":
        neurons = {}
        for k, nd in data.get("neurons", {}).items():
            neurons[k] = Neuron.from_dict(nd)
        return cls(group_type=data["group_type"], neurons=neurons)

    def _default_activation_pattern(self, source_key: str, strength: float) -> None:
        neuron = self.neurons.get(source_key)
        if neuron is None:
            return
        for target_key, weight in neuron.connections.items():
            target = self.neurons.get(target_key)
            if target is None:
                continue
            signal = strength * weight
            target.activation = min(target.activation + signal, 1.0)

    def add_neuron(self, neuron: Neuron) -> None:
        self.neurons[neuron.key] = neuron

    def activate(self, key: str, strength: float = 1.0) -> None:
        neuron = self.neurons.get(key)
        if neuron is None:
            return
        neuron.activation = min(neuron.activation + strength, 1.0)
        self.activation_pattern(key, strength)


class CoreNetwork:
    def __init__(self, classifier: Optional[RelationClassifier] = None):
        self.groups: Dict[str, RelationGroup] = {}
        self.classifier = classifier or RelationClassifier()
        self._synonym_group = RelationGroup(group_type="synonym")
        self._mapping_group = RelationGroup(group_type="mapping")
        self._analogy_group = RelationGroup(group_type="analogy")
        self.groups["synonym"] = self._synonym_group
        self.groups["mapping"] = self._mapping_group
        self.groups["analogy"] = self._analogy_group
        # Memory budget on the total number of connections across all groups.
        # The SNN stores connections as per-neuron dicts (sparse), but without a
        # bound the count still grows unbounded as more relations are trained.
        # Rather than truncating the *input* dataset, we keep training on all
        # samples and evict the weakest connections once over budget.
        # max_connections <= 0 means "unbounded" (legacy behavior).
        self.max_connections = limit_value("ai.core_network.max_connections", 200000)
        # Running connection tally — kept incrementally so we don't pay an
        # O(total_connections) recount on every adjust_connection call during
        # large training runs.
        self._conn_count = 0

    def forward(
        self,
        input_keys: List[str],
        context: Optional[Dict[str, object]] = None,
    ) -> Dict[str, float]:
        if not input_keys:
            return {}
        self.reset()
        activations: Dict[str, float] = {}

        for key in input_keys:
            for group_name, group in self.groups.items():
                if key in group.neurons:
                    group.activate(key, 1.0)

        for key in input_keys:
            for other_key in input_keys:
                if key >= other_key:
                    continue
                rel_type, confidence = self.classifier.classify_pair(
                    key, other_key, context=context
                )
                self._apply_relation_activation(
                    key, other_key, rel_type, confidence
                )

        propagated = self.compute_spike_propagation(
            active_keys=input_keys, max_hops=limit_value("ai.core_network.propagation_hops", 3), decay=behavior_threshold("ai.core_network.propagation_decay", 0.5)
        )
        activations.update(propagated)

        for group in self.groups.values():
            for n_key, neuron in group.neurons.items():
                if neuron.activation > neuron.threshold:
                    activations[n_key] = max(
                        activations.get(n_key, 0.0), neuron.activation
                    )

        return activations

    def add_relation(
        self, key1: str, relation_type: RelationType, key2: str, weight: float = 1.0
    ) -> None:
        if not key1 or not key2:
            logger.warning("Cannot add connection: empty key")
            return
        group = self._group_for_type(relation_type)
        if group is None:
            return
        for n_key in (key1, key2):
            if n_key not in group.neurons:
                group.add_neuron(Neuron(key=n_key, group_type=group.group_type))
        if key2 not in group.neurons[key1].connections:
            self._conn_count += 1
        group.neurons[key1].connections[key2] = weight
        if key1 not in group.neurons[key2].connections:
            self._conn_count += 1
        group.neurons[key2].connections[key1] = weight

    def add_directed(
        self, source_key: str, target_key: str, weight: float = 1.0
    ) -> None:
        if not source_key or not target_key:
            logger.warning("Cannot add directed connection: empty key")
            return
        group = self.groups.get("mapping")
        if group is None:
            return
        if source_key not in group.neurons:
            group.add_neuron(Neuron(key=source_key, group_type="mapping"))
        if target_key not in group.neurons:
            group.add_neuron(Neuron(key=target_key, group_type="mapping"))
        old = group.neurons[source_key].connections.get(target_key, 0.0)
        if target_key not in group.neurons[source_key].connections:
            self._conn_count += 1
        group.neurons[source_key].connections[target_key] = min(1.0, old + weight)
        if old > 0:
            group.neurons[target_key].connections[source_key] = max(0.0, old - behavior_threshold("ai.core_network.reverse_decay", 0.05))

    def get_activation(self, key: str) -> float:
        max_act = 0.0
        for group in self.groups.values():
            neuron = group.neurons.get(key)
            if neuron is not None and neuron.activation > max_act:
                max_act = neuron.activation
        return max_act

    def reset(self) -> None:
        for group in self.groups.values():
            for neuron in group.neurons.values():
                neuron.activation = 0.0

    def compute_spike_propagation(
        self,
        active_keys: List[str],
        max_hops: int = limit_value("ai.core_network.propagation_hops", 3),
        decay: float = behavior_threshold("ai.core_network.propagation_decay", 0.5),
        groups_scope: Optional[Dict[str, "RelationGroup"]] = None,
    ) -> Dict[str, float]:
        propagations: Dict[str, float] = {}
        queue: List[Tuple[str, float, int]] = [
            (k, 1.0, 0) for k in active_keys
        ]
        visited: Set[str] = set()
        scope = self.groups if groups_scope is None else groups_scope

        while queue:
            current_key, current_strength, hop = queue.pop(0)
            if hop >= max_hops:
                continue
            visited.add(current_key)

            for group in scope.values():
                neuron = group.neurons.get(current_key)
                if neuron is None:
                    continue
                for target_key, weight in neuron.connections.items():
                    if target_key in visited:
                        continue
                    new_strength = current_strength * weight * decay
                    if new_strength < threshold_value("ai.core_network.propagation_cutoff", 0.05):
                        continue
                    propagations[target_key] = max(
                        propagations.get(target_key, 0.0), new_strength
                    )
                    queue.append((target_key, new_strength, hop + 1))

        return propagations

    def _apply_relation_activation(
        self,
        key1: str,
        key2: str,
        rel_type: RelationType,
        confidence: float,
    ) -> None:
        group = self._group_for_type(rel_type)
        if group is None:
            return
        for n_key in (key1, key2):
            if n_key not in group.neurons:
                group.add_neuron(Neuron(key=n_key, group_type=group.group_type))
        w = confidence
        group.neurons[key1].connections[key2] = w
        group.neurons[key2].connections[key1] = w
        group.activate(key1, w)
        group.activate(key2, w)

    def train_step(
        self, examples: List[Tuple[str, str, float]]
    ) -> Dict[str, float]:
        correct = 0
        total_loss = 0.0
        changes = 0

        for key1, key2, expected_strength in examples:
            self.reset()
            self.forward([key1])
            actual = self.get_activation(key2)
            error = expected_strength - actual
            total_loss += abs(error)

            if (actual > threshold_value("ai.core_network.train_actual_threshold", 0.3) and expected_strength > threshold_value("ai.core_network.train_expected_threshold", 0.5)) or (
                actual <= threshold_value("ai.core_network.train_actual_threshold", 0.3) and expected_strength <= threshold_value("ai.core_network.train_expected_threshold", 0.5)
            ):
                correct += 1

            delta = self._compute_hebbian_delta(key1, key2, expected_strength)
            self.adjust_connection(key1, key2, delta)
            changes += 1

        n = len(examples)
        return {
            "loss": total_loss / max(n, 1),
            "accuracy": correct / max(n, 1),
            "connection_changes": changes,
        }

    def _count_connections(self) -> int:
        total = 0
        for group in self.groups.values():
            for neuron in group.neurons.values():
                total += len(neuron.connections)
        return total

    def _recompute_conn_count(self) -> None:
        self._conn_count = self._count_connections()

    def _evict_weakest(self) -> None:
        """Drop the globally weakest connections until back under budget.

        We never truncate the input dataset; instead we shed the least-strong
        learned associations so total memory stays bounded while the network
        has still trained on every sample.

        Eviction runs as a single O(total) scan that pops the bottom batch of
        connections (down to ~90% of budget) in one pass, rather than removing
        one connection per O(total) scan — which would be catastrophically slow
        during large training runs.
        """
        if self.max_connections <= 0:
            return
        if self._conn_count <= self.max_connections:
            return
        target = int(self.max_connections * 0.9)
        # Collect all connections with their weight into a flat list.
        all_conn: List[Tuple[float, str, str, str]] = []
        for gname, group in self.groups.items():
            for src, neuron in group.neurons.items():
                for tgt, w in neuron.connections.items():
                    all_conn.append((w, gname, src, tgt))
        if not all_conn:
            self._conn_count = 0
            return
        # Weakest connections have the smallest weight; sort ascending.
        all_conn.sort(key=lambda x: x[0])
        to_remove = len(all_conn) - target
        if to_remove <= 0:
            self._conn_count = self._count_connections()
            return
        for w, gname, src, tgt in all_conn[:to_remove]:
            grp = self.groups[gname]
            grp.neurons[src].connections.pop(tgt, None)
            if tgt in grp.neurons:
                grp.neurons[tgt].connections.pop(src, None)
        self._conn_count = target

    def adjust_connection(self, key1: str, key2: str, delta: float) -> None:
        # Check if connection already exists
        exists = any(
            key1 in group.neurons and key2 in group.neurons[key1].connections
            for group in self.groups.values()
        )
        if not exists:
            # Create new connection via add_relation if neither exists.
            # add_relation maintains _conn_count incrementally (two new edges).
            self.add_relation(key1, RelationType.MAPPING, key2, weight=max(0.0, min(delta, 1.0)))
            # Only new connections grow memory, so only they can breach budget.
            self._evict_weakest()
            return
        for group in self.groups.values():
            n1 = group.neurons.get(key1)
            n2 = group.neurons.get(key2)
            if n1 is None or n2 is None:
                continue
            current = n1.connections.get(key2, 0.0)
            updated = min(max(current + delta, 0.0), 1.0)
            n1.connections[key2] = updated
            n2.connections[key1] = updated
        # Existing-connection weight changes don't change the connection count,
        # so no eviction check is needed here.

    def get_trainable_parameters(self) -> Dict[str, Any]:
        params: Dict[str, Any] = {"neurons": {}, "connections": []}
        for group_name, group in self.groups.items():
            for n_key, neuron in group.neurons.items():
                params["neurons"][n_key] = {
                    "threshold": neuron.threshold,
                    "activation": neuron.activation,
                    "group": group_name,
                }
                for t_key, weight in neuron.connections.items():
                    params["connections"].append(
                        {"from": n_key, "to": t_key, "weight": weight, "group": group_name}
                    )
        return params

    def save_connections(self, path: str) -> None:
        """Save network connections to JSON."""
        import json
        import os

        conns = []
        for group_name, group in self.groups.items():
            for src_key, neuron in group.neurons.items():
                for tgt_key, weight in neuron.connections.items():
                    conns.append({
                        "source": src_key,
                        "target": tgt_key,
                        "weight": round(weight, 6),
                        "group": group_name,
                    })
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(conns, f, ensure_ascii=False, indent=2)

    def load_connections(self, path: str) -> int:
        """Load network connections from JSON."""
        import json

        with open(path, "r", encoding="utf-8") as f:
            conns = json.load(f)
        count = 0
        group_rel_map = {
            "synonym": RelationType.SYNONYM,
            "mapping": RelationType.MAPPING,
            "analogy": RelationType.ANALOGY,
        }
        for c in conns:
            rel_type = group_rel_map.get(c.get("group", "mapping"), RelationType.MAPPING)
            self.add_relation(c["source"], rel_type, c["target"], c.get("weight", 0.5))
            count += 1
        return count

    def _compute_hebbian_delta(
        self, key1: str, key2: str, expected_strength: float
    ) -> float:
        pre_act = self.get_activation(key1)
        post_act = self.get_activation(key2)
        hebbian = pre_act * post_act
        lr = learning_rate("ai.core_network.hebbian_lr", 0.05)
        return lr * (expected_strength * hebbian - behavior_threshold("ai.core_network.hebbian_regularization", 0.01))

    def _group_for_type(self, rel_type: RelationType) -> Optional[RelationGroup]:
        mapping = {
            RelationType.SYNONYM: "synonym",
            RelationType.ANTI_SYNONYM: "synonym",
            RelationType.MAPPING: "mapping",
            RelationType.ANTI_MAPPING: "mapping",
            RelationType.ANALOGY: "analogy",
            RelationType.ANTI_ANALOGY: "analogy",
        }
        group_name = mapping.get(rel_type)
        return self.groups.get(group_name) if group_name else None

    def _build_sequential_scope(self, path_type: str) -> Dict[str, "RelationGroup"]:
        if path_type == "sequence":
            return {k: g for k, g in self.groups.items() if k == "mapping"}
        return self.groups

    def _activate_visible_keys(
        self, visible_keys: List[str], groups_scope: Dict[str, "RelationGroup"]
    ) -> None:
        for key in visible_keys:
            for group in groups_scope.values():
                if key in group.neurons:
                    group.activate(key, 1.0)

    def _apply_recency_bias(
        self, visible_keys: List[str], groups_scope: Dict[str, "RelationGroup"]
    ) -> None:
        num_visible = len(visible_keys)
        if num_visible > 0:
            for pos, key in enumerate(visible_keys):
                recency = 1.0 + behavior_threshold("ai.core_network.recency_factor", 0.15) * pos / max(num_visible, 1)
                for group in groups_scope.values():
                    neuron = group.neurons.get(key)
                    if neuron is not None:
                        neuron.activation = min(neuron.activation * recency, 1.0)

    def _collect_threshold_activations(
        self, groups_scope: Dict[str, "RelationGroup"], activations: Dict[str, float]
    ) -> Dict[str, float]:
        for group in groups_scope.values():
            for n_key, neuron in group.neurons.items():
                if neuron.activation > neuron.threshold:
                    activations[n_key] = max(
                        activations.get(n_key, 0.0), neuron.activation
                    )
        return activations

    def forward_sequential(
        self,
        input_keys: List[str],
        current_position: int,
        path_type: str = "semantic",
    ) -> Dict[str, float]:
        if not input_keys or current_position < 0:
            return {}

        groups_scope = self._build_sequential_scope(path_type)

        self.reset()
        activations: Dict[str, float] = {}

        visible_keys = input_keys[: current_position + 1]

        self._activate_visible_keys(visible_keys, groups_scope)
        self._apply_recency_bias(visible_keys, groups_scope)

        propagated = self.compute_spike_propagation(
            active_keys=visible_keys, max_hops=limit_value("ai.core_network.sequential_hops", 2), decay=behavior_threshold("ai.core_network.sequential_decay", 0.3),
            groups_scope=groups_scope if path_type == "sequence" else None,
        )
        activations.update(propagated)

        return self._collect_threshold_activations(groups_scope, activations)

    # ------------------------------------------------------------------
    # Relational chain resolution (offline, graph-based multi-hop reasoning)
    # ------------------------------------------------------------------

    def resolve_relational_chain(
        self,
        edges: List[Tuple[str, str, float]],
        query_entities: List[str],
        ask_max: bool = True,
    ) -> Optional[str]:
        """Resolve a transitive relational chain over explicitly stated edges.

        Delegates to the shared ``ai.reasoning.relational_chain`` transitive
        closure. This is a genuine multi-hop graph derivation, independent of any
        pre-trained associations. Used as a fallback when the deterministic
        symbolic reasoner does not match a query but the query itself states a
        relational structure (e.g. "X warmer than Y, Y warmer than Z, warmest?").

        Args:
            edges: List of (subject, object, weight>0) directed comparisons
                   where a larger weight means "subject is greater in the
                   compared dimension". For a "lesser" comparator the edge is
                   reversed by the caller.
            query_entities: candidate entity names appearing in the question.
            ask_max: If True resolve the entity that dominates all others
                     (greatest); if False resolve the least (smallest).

        Returns:
            The resolved entity string, or None if no unique solution.
        """
        from ai.reasoning.relational_chain import resolve_relational_chain as _resolve

        return _resolve(edges, query_entities, ask_max=ask_max)

    def sync_from_dictionary(self, dictionary: "DictionaryLayer") -> int:
        count = 0
        rel_map = {
            "synonym": RelationType.SYNONYM,
            "mapping": RelationType.MAPPING,
            "analogy": RelationType.ANALOGY,
            "antonym": RelationType.ANTI_SYNONYM,
        }
        for key, entry in dictionary.entries.items():
            for rel_type_str, targets in entry.relations.items():
                rel_type = rel_map.get(rel_type_str)
                if rel_type is None:
                    continue
                for target in targets:
                    if target in dictionary.entries:
                        self.add_relation(key, rel_type, target, weight=behavior_threshold("ai.core_network.sync_weight", 0.5))
                        count += 1
        logger.info("Synced %d relations from dictionary to network", count)
        return count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "groups": {name: g.to_dict() for name, g in self.groups.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], classifier: Optional[RelationClassifier] = None) -> "CoreNetwork":
        net = cls(classifier=classifier)
        for name, gd in data.get("groups", {}).items():
            net.groups[name] = RelationGroup.from_dict(gd)
        return net
