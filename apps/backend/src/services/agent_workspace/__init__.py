"""代理工作區（Agent Workspace）：AI 操作應用程式的完整閉環＋樹狀上下文治理。"""

from services.agent_workspace.agent import (
    AgentWorkspace,
    BrowserAgent,
    DesktopAgent,
    build_default_workspace,
)
from services.agent_workspace.app_session import (
    ActionSpec,
    AppAdapter,
    AppSessionManager,
)
from services.agent_workspace.context_tree import ContextNode, ContextTree

__all__ = [
    "ActionSpec",
    "AgentWorkspace",
    "AppAdapter",
    "AppSessionManager",
    "BrowserAgent",
    "ContextNode",
    "ContextTree",
    "DesktopAgent",
    "build_default_workspace",
]
