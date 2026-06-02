import logging
import operator
from collections import deque
from typing import Optional

from .models import ModuleDescriptor, ModuleStatus, ModuleInstance, DependencySpec

logger = logging.getLogger(__name__)


class CycleError(Exception):
    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        super().__init__(f"Cycle detected: {' -> '.join(cycle)}")


class DependencyResolver:
    def resolve(self, descriptors: list[ModuleDescriptor]) -> list[ModuleDescriptor]:
        graph = self._build_graph(descriptors)
        sorted_names = self._topological_sort(graph)
        name_map = {d.name: d for d in descriptors}
        return [name_map[name] for name in sorted_names]

    def _build_graph(self, descriptors: list[ModuleDescriptor]) -> dict[str, set[str]]:
        names = {d.name for d in descriptors}
        graph: dict[str, set[str]] = {d.name: set() for d in descriptors}
        for descriptor in descriptors:
            for dep in descriptor.depends_on.required:
                if dep in names:
                    graph[dep].add(descriptor.name)
        return graph

    def _topological_sort(self, graph: dict[str, set[str]]) -> list[str]:
        in_degree: dict[str, int] = {node: 0 for node in graph}
        for node in graph:
            for neighbor in graph[node]:
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

        queue = deque([node for node in graph if in_degree[node] == 0])
        sorted_nodes: list[str] = []

        while queue:
            node = queue.popleft()
            sorted_nodes.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        remaining = [node for node in graph if in_degree[node] > 0]
        if remaining:
            cycle = self._detect_cycle(graph)
            raise CycleError(cycle if cycle else remaining)

        return sorted_nodes

    def _detect_cycle(self, graph: dict[str, set[str]]) -> Optional[list[str]]:
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str, path: list[str]) -> Optional[list[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    result = dfs(neighbor, path)
                    if result is not None:
                        return result
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
            path.pop()
            rec_stack.discard(node)
            return None

        for node in graph:
            if node not in visited:
                result = dfs(node, [])
                if result is not None:
                    return result
        return None

    @staticmethod
    def _check_constraint(actual: str, constraint: str) -> bool:
        if not constraint:
            return True
        constraint = constraint.strip()
        ops = {
            ">=": operator.ge, "<=": operator.le,
            ">": operator.gt, "<": operator.lt,
            "==": operator.eq,
        }
        op = operator.eq
        ver = constraint
        for prefix in (">=", "<=", ">", "<", "=="):
            if constraint.startswith(prefix):
                op = ops[prefix]
                ver = constraint[len(prefix):].strip()
                break
        try:
            actual_parts = tuple(int(x) for x in actual.split("."))
            ver_parts = tuple(int(x) for x in ver.split("."))
            max_len = max(len(actual_parts), len(ver_parts))
            actual_parts = actual_parts + (0,) * (max_len - len(actual_parts))
            ver_parts = ver_parts + (0,) * (max_len - len(ver_parts))
            return op(actual_parts, ver_parts)
        except (ValueError, TypeError):
            logger.warning(f"Version constraint check failed for actual={actual}, ver={ver}", exc_info=True)
            return actual == ver

    def check_deps(self, descriptor: ModuleDescriptor, existing: list[ModuleDescriptor]) -> list[str]:
        existing_map = {d.name: d for d in existing}
        missing: list[str] = []
        for dep in descriptor.depends_on.required:
            if dep not in existing_map:
                missing.append(dep)
            else:
                constraint = descriptor.constraints.get(dep)
                if constraint and not self._check_constraint(existing_map[dep].version, constraint):
                    missing.append(f"{dep} (needs {constraint}, has {existing_map[dep].version})")
        return missing

    def missing_optional(self, descriptor: ModuleDescriptor, existing: list[ModuleDescriptor]) -> list[str]:
        existing_names = {d.name for d in existing}
        return [dep for dep in descriptor.depends_on.optional if dep not in existing_names]
