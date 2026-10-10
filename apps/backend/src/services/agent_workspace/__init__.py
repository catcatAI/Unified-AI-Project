"""代理工作區（Agent Workspace）：AI 操作應用程式的完整閉環＋樹狀上下文治理。"""

from services.agent_workspace.agent import (
    MOUNT_KIND_ALIASES,
    MOUNT_KIND_REGISTRY,
    AgentWorkspace,
    BrowserAgent,
    DesktopAgent,
    EdaWorkspaceAdapter,
    FilesAdapter,
    ShellAdapter,
    build_default_workspace,
)
from services.agent_workspace.app_session import (
    ActionSpec,
    AppAdapter,
    AppSessionManager,
)
from services.agent_workspace.context_tree import ContextNode, ContextTree
from services.agent_workspace.global_tree import (
    GlobalContextProviders,
    GlobalContextTree,
    UnifiedWorkspace,
)

__all__ = [
    "ActionSpec",
    "AgentWorkspace",
    "AppAdapter",
    "AppSessionManager",
    "BrowserAgent",
    "ContextNode",
    "ContextTree",
    "DesktopAgent",
    "EdaWorkspaceAdapter",
    "FilesAdapter",
    "GlobalContextProviders",
    "GlobalContextTree",
    "MOUNT_KIND_ALIASES",
    "MOUNT_KIND_REGISTRY",
    "ShellAdapter",
    "UnifiedWorkspace",
    "build_default_workspace",
]
