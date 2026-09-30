"""樹狀上下文（Context Tree）：AI 操作應用程式時的上下文治理。

雙視圖規則：
- **全貌視圖（overview）**：AI 完全不清楚狀況時呈現樹狀全貌——**唯讀**，
  只能看與定位，不能執行。
- **執行器視圖（focus）**：切換到某節點後，只顯示該節點所在的樹狀分層
  （路徑列＋子節點＋可用指令白名單），AI 依需求切層並執行確定指令。

上下文預算：每個視圖有字元上限，超過時子樹摺疊為「…還有 N 個節點」，
強迫 AI 下鑽而非一次吞下整棵樹——保護 LLM 注意力與訓練收斂。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 單一視圖的字元預算（第二道防線；主要約束是 MAX_VIEW_LINES 行數上限）
DEFAULT_VIEW_BUDGET = 8000
# 單層最多展開的子節點數（超出摺疊，需下鑽）
DEFAULT_CHILDREN_LIMIT = 12
# 單一視圖的行數上限：全貌與執行器視圖都不得超過（保護 LLM 注意力）
MAX_VIEW_LINES = 100


@dataclass
class ContextNode:
    """樹狀上下文的一個節點（應用/面板/檔案/控制項…）。"""

    id: str
    label: str
    kind: str  # "workspace" | "app" | "session" | "file" | "pane" | ...
    summary: str = ""  # 一行狀態摘要（全貌視圖顯示）
    children: List["ContextNode"] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)  # 該節點可執行的指令白名單
    readonly: bool = True  # 全貌視圖一律唯讀；執行視圖由節點性質決定
    meta: Dict[str, Any] = field(default_factory=dict)
    preview: List[str] = field(default_factory=list)  # 內容採樣（執行器視圖顯示的資料樣本）

    def find(self, node_id: str) -> Optional["ContextNode"]:
        if self.id == node_id:
            return self
        for child in self.children:
            found = child.find(node_id)
            if found is not None:
                return found
        return None

    def path_to(self, node_id: str) -> List["ContextNode"]:
        """回傳從根到目標節點的路徑（含兩端）；找不到回傳空清單。"""
        if self.id == node_id:
            return [self]
        for child in self.children:
            sub = child.path_to(node_id)
            if sub:
                return [self] + sub
        return []


class ContextTree:
    """一棵上下文樹：負責產生全貌視圖與執行器視圖。"""

    def __init__(
        self,
        root: ContextNode,
        view_budget: int = DEFAULT_VIEW_BUDGET,
        children_limit: int = DEFAULT_CHILDREN_LIMIT,
    ) -> None:
        self.root = root
        self._budget = view_budget
        self._children_limit = children_limit

    # ---------- 全貌視圖（唯讀） ----------

    def overview(self, max_depth: int = 3) -> Dict[str, Any]:
        """樹狀全貌（唯讀）：節點摘要＋摺疊計數，不含任何執行指令。

        行數上限 MAX_VIEW_LINES：超過時略去整支分支並標記（不粗暴切字元），
        引導 AI 用 focus 下鑽；字元預算為第二道防線。
        """
        lines: List[str] = []
        omitted = 0

        def render(node: ContextNode, depth: int, max_depth: int) -> bool:
            nonlocal omitted
            if depth > max_depth:
                return False
            if len(lines) >= MAX_VIEW_LINES - 2:  # 保留標記行
                omitted += 1
                return True
            indent = "  " * depth
            # 🔧＝有指令白名單且非唯讀（聚焦後可執行）；否則唯讀 🔒
            flag = "🔧" if node.commands and not node.readonly else "🔒"
            suffix = f" — {node.summary}" if node.summary else ""
            lines.append(f"{indent}{flag} {node.label} [{node.id}]{suffix}")
            rendered = 0
            hidden = 0
            truncated_any = False
            for child in node.children:
                if rendered >= self._children_limit:
                    hidden += 1
                    continue
                if render(child, depth + 1, max_depth):
                    truncated_any = True
                rendered += 1
            if hidden:
                lines.append(f"{indent}  …還有 {hidden} 個子節點（下鑽查看）")
                truncated_any = True
            return truncated_any

        truncated = render(self.root, 0, max_depth)
        if omitted:
            lines.append(
                f"…（超過 {MAX_VIEW_LINES} 行上限，略去 {omitted} 個分支——請用 focus 下鑽）"
            )
            truncated = True
        view = "\n".join(lines)
        if len(view) > self._budget:
            lines = lines[: max(1, self._budget // 80)]
            lines.append("…（全貌超過上下文預算，請用更精確的定位）")
            view = "\n".join(lines)
            truncated = True
        return {
            "view": "overview",
            "readonly": True,
            "truncated": truncated,
            "lines": len(view.splitlines()),
            "text": view,
            "budget_chars": self._budget,
        }

    # ---------- 執行器視圖（分層） ----------

    def focus(self, node_id: str) -> Dict[str, Any]:
        """執行器視圖：路徑列＋當前層子節點＋該層可用指令。"""
        path = self.root.path_to(node_id)
        if not path:
            return {
                "view": "focus",
                "error": f"節點 {node_id} 不存在；請先回全貌重新定位",
                "readonly": True,
                "text": "",
            }
        node = path[-1]
        lines: List[str] = ["路徑: " + " → ".join(f"{n.label}[{n.id}]" for n in path)]
        if node.summary:
            lines.append(f"摘要: {node.summary}")
        lines.append("")
        if node.commands:
            lines.append(f"可用指令: {', '.join(node.commands)}")
        else:
            lines.append("此層無可執行指令（唯讀層）——可下鑽子節點")
        if node.children:
            lines.append("")
            lines.append("子節點:")
            hidden = 0
            for child in node.children[: self._children_limit]:
                suffix = f" — {child.summary}" if child.summary else ""
                lines.append(f"  {child.label} [{child.id}]{suffix}")
            hidden = len(node.children) - min(len(node.children), self._children_limit)
            if hidden:
                lines.append(f"  …還有 {hidden} 個子節點")
        if node.preview:
            lines.append("")
            lines.append("內容採樣:")
            for sample in node.preview[:8]:
                lines.append(f"  {sample[:60]}")
        view = "\n".join(lines)
        if len(view) > self._budget:
            view = view[: self._budget] + "\n…（超出上下文預算）"
        return {
            "view": "focus",
            "node_id": node.id,
            "readonly": node.readonly,
            "commands": list(node.commands),
            "lines": len(view.splitlines()),
            "text": view,
            "budget_chars": self._budget,
        }
