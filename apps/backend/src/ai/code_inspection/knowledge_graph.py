"""
Angela Knowledge Graph - 代碼結構知識圖譜
==========================================

純演算法構建，不依賴 LLM。
將代碼庫結構轉化為可查詢的圖譜。

節點類型：
  - FileNode: 文件
  - ClassNode: 類
  - FunctionNode: 函數
  - MethodNode: 方法
  - ImportNode: import 語句

邊類型：
  - CONTAINS: 文件包含類/函數
  - IMPORTS: 文件導入模組
  - CALLS: 函數調用其他函數
  - INHERITS: 類繼承關係
  - DECORATED_BY: 函數被裝飾器標記

Author: Angela AI Development Team
Version: 6.2.1
"""

from __future__ import annotations
import ast
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from pathlib import Path

logger = logging.getLogger("angela_knowledge_graph")


@dataclass
class GraphNode:
    id: str
    type: str
    name: str
    file: str
    lineno: int = 0
    end_lineno: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    outgoing: List[str] = field(default_factory=list)
    incoming: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash(self.id)


@dataclass
class GraphEdge:
    source: str
    target: str
    type: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    """
    代碼知識圖譜
    """

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._edge_map: Dict[str, List[str]] = {}
        self._file_to_node_ids: Dict[str, Set[str]] = {}

    def build_from_directory(self, max_depth: int = 5) -> int:
        """
        從目錄構建圖譜

        Returns:
            構建的節點數量
        """
        python_files = list(self.root_path.rglob("*.py"))
        count = 0

        for filepath in python_files:
            try:
                self._build_file_graph(filepath)
                count += 1
                if count % 50 == 0:
                    logger.info(f"[KnowledgeGraph] Processed {count} files...")
            except Exception as e:
                logger.warning(f"[KnowledgeGraph] Failed to parse {filepath}: {e}", exc_info=True)

        self._build_call_relationships()
        logger.info(f"[KnowledgeGraph] Built graph with {len(self.nodes)} nodes, {len(self.edges)} edges")
        return len(self.nodes)

    def _build_file_graph(self, filepath: Path) -> None:
        """為單個文件構建圖譜"""
        try:
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except Exception:
            logger.warning(f"[KnowledgeGraph] Failed to parse {filepath}: fallback skip", exc_info=True)
            return

        file_node = GraphNode(
            id=f"file:{filepath}",
            type="file",
            name=filepath.name,
            file=str(filepath),
            metadata={"size": len(source), "lines": source.count('\n') + 1},
        )
        self._add_node(file_node)
        self._track_file_node(filepath, file_node.id)

        imports = self._extract_imports(tree, str(filepath))
        for imp in imports:
            self._add_node(imp)
            self._add_edge(GraphEdge(source=file_node.id, target=imp.id, type="IMPORTS"))

        classes = self._extract_classes(tree, str(filepath))
        for cls in classes:
            self._add_node(cls)
            self._add_edge(GraphEdge(source=file_node.id, target=cls.id, type="CONTAINS"))

            for method in cls.methods:
                self._add_node(method)
                self._add_edge(GraphEdge(source=cls.id, target=method.id, type="CONTAINS"))

        functions = self._extract_functions(tree, str(filepath))
        for func in functions:
            self._add_node(func)
            self._add_edge(GraphEdge(source=file_node.id, target=func.id, type="CONTAINS"))

    def _add_node(self, node: GraphNode) -> None:
        if node.id not in self.nodes:
            self.nodes[node.id] = node

    def _add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)
        if edge.source not in self._edge_map:
            self._edge_map[edge.source] = []
        self._edge_map[edge.source].append(edge.target)

    def _track_file_node(self, filepath: Path, node_id: str) -> None:
        key = str(filepath)
        if key not in self._file_to_node_ids:
            self._file_to_node_ids[key] = set()
        self._file_to_node_ids[key].add(node_id)

    def _extract_imports(self, tree: ast.AST, filepath: str) -> List[GraphNode]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(GraphNode(
                        id=f"import:{alias.name}:{filepath}",
                        type="import",
                        name=alias.name,
                        file=filepath,
                        lineno=node.lineno,
                    ))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(GraphNode(
                        id=f"import:from:{node.module}:{filepath}",
                        type="import",
                        name=f"from {node.module}",
                        file=filepath,
                        lineno=node.lineno,
                    ))
        return imports

    def _extract_classes(self, tree: ast.AST, filepath: str) -> List[GraphNode]:
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                base_names = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_names.append(base.id)

                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        params = [a.arg for a in item.args.args]
                        method_node = GraphNode(
                            id=f"method:{node.name}.{item.name}:{filepath}",
                            type="method",
                            name=item.name,
                            file=filepath,
                            lineno=item.lineno,
                            end_lineno=item.end_lineno or item.lineno,
                            metadata={"params": params, "decorators": [d.func.id if isinstance(d, ast.Name) else str(d) for d in item.decorator_list]},
                        )
                        methods.append(method_node)

                class_node = GraphNode(
                    id=f"class:{node.name}:{filepath}",
                    type="class",
                    name=node.name,
                    file=filepath,
                    lineno=node.lineno,
                    end_lineno=node.end_lineno or node.lineno,
                    metadata={"bases": base_names, "method_count": len(methods)},
                )
                class_node.metadata["methods"] = methods
                classes.append(class_node)

        return classes

    def _extract_functions(self, tree: ast.AST, filepath: str) -> List[GraphNode]:
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not isinstance(node.parent, ast.ClassDef) if hasattr(node, 'parent') else True:
                if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)):
                    params = [a.arg for a in node.args.args]
                    func_node = GraphNode(
                        id=f"func:{node.name}:{filepath}",
                        type="function",
                        name=node.name,
                        file=filepath,
                        lineno=node.lineno,
                        end_lineno=node.end_lineno or node.lineno,
                        metadata={"params": params, "decorators": [d.func.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list]},
                    )
                    functions.append(func_node)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        params = [a.arg for a in item.args.args]
                        func_node = GraphNode(
                            id=f"func:{item.name}:{filepath}",
                            type="function",
                            name=item.name,
                            file=filepath,
                            lineno=item.lineno,
                            end_lineno=item.end_lineno or item.lineno,
                            metadata={"params": params, "decorators": [d.func.id if isinstance(d, ast.Name) else str(d) for d in item.decorator_list]},
                        )
                        functions.append(func_node)

        return functions

    def _build_call_relationships(self) -> None:
        """遍歷所有函數，建立調用關係"""
        for node_id, node in self.nodes.items():
            if node.type not in ("function", "method"):
                continue

            try:
                filepath = Path(node.file)
                source = filepath.read_text(encoding="utf-8")
                ast.parse(source)
            except Exception:
                logger.warning("Failed to read/parse file %s, skipping", node.file if hasattr(node, 'file') else 'unknown', exc_info=True)
                continue

            source_lines = source.split('\n')
            if node.lineno <= 0 or node.lineno > len(source_lines):
                continue

            func_source = '\n'.join(source_lines[node.lineno - 1:node.end_lineno - 1] if node.end_lineno > node.lineno else [source_lines[node.lineno - 1]])
            try:
                func_tree = ast.parse(func_source)
            except Exception:
                logger.warning("Failed to parse function source for %s", node.name if hasattr(node, 'name') else 'unknown', exc_info=True)
                continue

            for child in ast.walk(func_tree):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        called_name = child.func.id
                        called_id = f"func:{called_name}:{node.file}"
                        if called_id in self.nodes:
                            self._add_edge(GraphEdge(
                                source=node_id,
                                target=called_id,
                                type="CALLS",
                                metadata={"lineno": getattr(child, 'lineno', 0)},
                            ))
                            if node_id in self.nodes:
                                self.nodes[node_id].outgoing.append(called_id)
                            if called_id in self.nodes:
                                self.nodes[called_id].incoming.append(node_id)
            break

    def find_node(self, name: str, type_filter: Optional[str] = None) -> List[GraphNode]:
        """按名稱查找節點"""
        results = []
        for node in self.nodes.values():
            if name in node.name:
                if type_filter is None or node.type == type_filter:
                    results.append(node)
        return results

    def get_dependencies(self, node_id: str) -> List[GraphNode]:
        """獲取節點的依賴（被誰調用）"""
        if node_id not in self.nodes:
            return []
        return [self.nodes[nid] for nid in self.nodes[node_id].incoming if nid in self.nodes]

    def get_dependents(self, node_id: str) -> List[GraphNode]:
        """獲取節點的依賴（調用誰）"""
        if node_id not in self.nodes:
            return []
        return [self.nodes[nid] for nid in self.nodes[node_id].outgoing if nid in self.nodes]

    def find_cycles(self) -> List[List[str]]:
        """檢測循環依賴"""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node_id: str, path: List[str]) -> None:
            """Execute the dfs operation."""
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in self.nodes.get(node_id, GraphNode("", "", "", "")).outgoing:
                if neighbor not in visited:
                    dfs(neighbor, path + [neighbor])
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])

            rec_stack.remove(node_id)

        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id, [node_id])

        return cycles

    def get_module_structure(self) -> Dict[str, List[str]]:
        """獲取模組結構"""
        structure: Dict[str, List[str]] = {}
        for node in self.nodes.values():
            if node.type == "file":
                dir_name = str(Path(node.file).parent)
                if dir_name not in structure:
                    structure[dir_name] = []
                structure[dir_name].append(node.name)
        return structure

    def export_to_dict(self) -> Dict[str, Any]:
        """導出為字典（用於序列化）"""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "name": n.name,
                    "file": n.file,
                    "lineno": n.lineno,
                    "metadata": n.metadata,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {"source": e.source, "target": e.target, "type": e.type, "weight": e.weight}
                for e in self.edges
            ],
        }

    def get_statistics(self) -> Dict[str, Any]:
        """獲取圖譜統計"""
        type_counts = {}
        for node in self.nodes.values():
            type_counts[node.type] = type_counts.get(node.type, 0) + 1

        edge_types = {}
        for edge in self.edges:
            edge_types[edge.type] = edge_types.get(edge.type, 0) + 1

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "node_types": type_counts,
            "edge_types": edge_types,
            "files": type_counts.get("file", 0),
            "classes": type_counts.get("class", 0),
            "functions": type_counts.get("function", 0),
            "methods": type_counts.get("method", 0),
        }


class GraphQueryEngine:
    """
    圖譜查詢引擎 — 在知識圖譜上進行複雜查詢
    """

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    def find_functions_called_by(self, func_name: str) -> List[GraphNode]:
        """查找某函數調用的所有函數"""
        nodes = self.graph.find_node(func_name, type_filter="function")
        results = []
        for node in nodes:
            for called_id in node.outgoing:
                if called_id in self.graph.nodes:
                    results.append(self.graph.nodes[called_id])
        return results

    def find_callers_of(self, func_name: str) -> List[GraphNode]:
        """查找所有調用某函數的函數"""
        results = []
        for node in self.graph.nodes.values():
            if func_name in node.name and node.type in ("function", "method"):
                for caller_id in node.incoming:
                    if caller_id in self.graph.nodes:
                        results.append(self.graph.nodes[caller_id])
        return results

    def find_files_in_module(self, module_path: str) -> List[GraphNode]:
        """查找某模組下的所有文件"""
        results = []
        for node in self.graph.nodes.values():
            if node.type == "file" and module_path in node.file:
                results.append(node)
        return results

    def find_class_methods(self, class_name: str) -> List[GraphNode]:
        """查找某類的所有方法"""
        results = []
        for node in self.graph.nodes.values():
            if node.type == "method" and class_name in node.id:
                results.append(node)
        return results

    def find_public_api(self, module_path: str) -> List[GraphNode]:
        """查找某模組的公開 API（不含 _ 前綴）"""
        results = []
        for node in self.graph.nodes.values():
            if node.type == "function" and module_path in node.file:
                if not node.name.startswith("_"):
                    results.append(node)
        return results

    def find_complex_functions(self, min_complexity: float = 10.0) -> List[GraphNode]:
        """查找複雜度超過閾值的函數"""
        results = []
        for node in self.graph.nodes.values():
            if node.type in ("function", "method"):
                complexity = node.metadata.get("complexity", 0)
                if complexity >= min_complexity:
                    results.append(node)
        return sorted(results, key=lambda n: n.metadata.get("complexity", 0), reverse=True)