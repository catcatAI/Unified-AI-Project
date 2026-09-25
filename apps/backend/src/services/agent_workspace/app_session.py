"""應用程式會話（App Session）：AI 操作應用的完整閉環。

生命週期狀態機：
    closed → open → (clean ⇄ dirty) → closing → closed

閉環步驟（每一步都記入學習日誌——教學、探索、成功、失敗都是學習資料）：
    1. open  開啟應用（desktop / browser…）
    2. read  讀取當前狀態（AI 可辨識的結構化快照）
    3. act   執行操作（危險操作需 confirm 確認門）
    4. save  保存（dirty → clean）
    5. close 關閉（有未保存變更時回 pending_confirmation，需 confirm=True）

設計原則：
- 與具體應用解耦：應用能力以 AppAdapter 注入（desktop / browser 各一）。
- 確認門（confirm gate）：危險操作第一次呼叫只回 pending_confirmation，
  AI 必須帶 confirm=True 重送——避免 LLM 一時誤判直接破壞。
- 學習日誌：JSON Lines，寫入 data/agent_workspace/learning_log.jsonl，
  每行含 ts/action/target/outcome/lesson/source，供後續學習器收斂。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# 學習日誌預設路徑（專案慣例：相對 data/ 目錄）
DEFAULT_LOG_PATH = Path("data/agent_workspace/learning_log.jsonl")

# 會話狀態
STATE_CLOSED = "closed"
STATE_OPEN = "open"
STATE_DIRTY = "dirty"
STATE_CLOSING = "closing"


@dataclass
class ActionSpec:
    """一條應用能力：名稱＋摘要＋是否危險（危險＝需過確認門）。"""

    name: str
    summary: str
    dangerous: bool = False


AsyncHandler = Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]


class AppAdapter:
    """應用能力介面：把具體控制器（DesktopInteraction / BrowserController…）
    包裝成「指令白名單＋執行器」。測試可注入假 adapter。"""

    app_id: str = ""
    label: str = ""

    def __init__(self) -> None:
        self._handlers: Dict[str, AsyncHandler] = {}
        self._specs: Dict[str, ActionSpec] = {}

    # -- 註冊能力 -------------------------------------------------------

    def register(self, spec: ActionSpec, handler: AsyncHandler) -> None:
        self._specs[spec.name] = spec
        self._handlers[spec.name] = handler

    def specs(self) -> List[ActionSpec]:
        return list(self._specs.values())

    def has(self, action: str) -> bool:
        return action in self._handlers

    def is_dangerous(self, action: str) -> bool:
        spec = self._specs.get(action)
        return bool(spec and spec.dangerous)

    async def run(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        handler = self._handlers.get(action)
        if handler is None:
            return {"ok": False, "error": f"未知指令：{action}"}
        return await handler(params)

    # -- 狀態快照（AI 識別用） ------------------------------------------

    async def read_state(self) -> Dict[str, Any]:
        """回傳應用當前狀態的結構化摘要（供 AI 辨識）。"""
        return {"app_id": self.app_id, "label": self.label}


@dataclass
class SessionRecord:
    """一個開啟中的應用會話。"""

    session_id: str
    app_id: str
    state: str = STATE_OPEN
    dirty: bool = False
    opened_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_result: Dict[str, Any] = field(default_factory=dict)
    op_count: int = 0

    def snapshot(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "app_id": self.app_id,
            "state": self.state,
            "dirty": self.dirty,
            "opened_at": self.opened_at,
            "op_count": self.op_count,
        }


class AppSessionManager:
    """應用會話管理器：閉環生命週期＋確認門＋學習日誌。"""

    def __init__(
        self,
        adapters: Optional[Dict[str, AppAdapter]] = None,
        log_path: Path = DEFAULT_LOG_PATH,
    ) -> None:
        self._adapters: Dict[str, AppAdapter] = adapters or {}
        self._log_path = log_path
        self._sessions: Dict[str, SessionRecord] = {}
        self._counter = 0

    # ---------- 查詢 ----------

    def available_apps(self) -> List[Dict[str, Any]]:
        """可開啟的應用清單（含指令白名單摘要）。"""
        apps: List[Dict[str, Any]] = []
        for app_id, adapter in self._adapters.items():
            apps.append(
                {
                    "app_id": app_id,
                    "label": adapter.label,
                    "commands": [s.name for s in adapter.specs()],
                }
            )
        return apps

    def get_session(self, app_id: str) -> Optional[SessionRecord]:
        return self._sessions.get(app_id)

    # ---------- 閉環：open → read → act → save → close ----------

    async def open_app(self, app_id: str, purpose: str = "", source: str = "teaching") -> Dict[str, Any]:
        """開啟應用會話。"""
        adapter = self._adapters.get(app_id)
        if adapter is None:
            self._log("open", app_id, "failed", f"無此應用：{app_id}", source)
            return {"ok": False, "error": f"無此應用：{app_id}"}
        if app_id in self._sessions:
            self._log("open", app_id, "failed", "會話已開啟", source)
            return {"ok": False, "error": f"會話已開啟：{app_id}"}
        self._counter += 1
        record = SessionRecord(session_id=f"{app_id}:{self._counter}", app_id=app_id)
        self._sessions[app_id] = record
        self._log("open", app_id, "ok", purpose or "開啟應用", source)
        commands = [s.name for s in adapter.specs()]
        return {"ok": True, "session": record.snapshot(), "commands": commands}

    async def read_app(self, app_id: str) -> Dict[str, Any]:
        """讀取應用當前狀態（AI 識別）。"""
        record = self._sessions.get(app_id)
        adapter = self._adapters.get(app_id)
        if record is None or adapter is None:
            return {"ok": False, "error": f"會話未開啟：{app_id}"}
        state = await adapter.read_state()
        self._log("read", app_id, "ok", "讀取狀態", "exploration")
        return {"ok": True, "session": record.snapshot(), "state": state}

    async def act(
        self,
        app_id: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        confirm: bool = False,
        source: str = "exploration",
    ) -> Dict[str, Any]:
        """在會話上執行指令。危險指令需 confirm=True 才會真正執行。"""
        record = self._sessions.get(app_id)
        adapter = self._adapters.get(app_id)
        if record is None or adapter is None:
            self._log(f"act:{action}", app_id, "failed", "會話未開啟", source)
            return {"ok": False, "error": f"會話未開啟：{app_id}"}
        if not adapter.has(action):
            self._log(f"act:{action}", app_id, "failed", "白名單外指令", source)
            return {"ok": False, "error": f"此層無指令 {action}；可用：{[s.name for s in adapter.specs()]}"}
        if adapter.is_dangerous(action) and not confirm:
            # 確認門：第一次只回 pending_confirmation，不執行
            self._log(f"act:{action}", app_id, "pending", "危險操作待確認", source)
            return {
                "ok": False,
                "status": "pending_confirmation",
                "confirm_required": True,
                "message": f"指令 {action} 為危險操作，請帶 confirm=True 重送",
            }
        try:
            result = await adapter.run(action, params or {})
        except Exception as exc:  # 學習資料：失敗也要記
            self._log(f"act:{action}", app_id, "failed", str(exc), source)
            return {"ok": False, "error": f"執行失敗：{exc}"}
        record.op_count += 1
        record.last_result = result
        if not result.get("ok", True):
            self._log(f"act:{action}", app_id, "failed", str(result.get("error", "")), source)
            return result
        record.state = STATE_DIRTY
        record.dirty = True
        self._log(f"act:{action}", app_id, "ok", "執行成功", source)
        return {"ok": True, "session": record.snapshot(), "result": result}

    async def save_app(self, app_id: str) -> Dict[str, Any]:
        """保存會話（dirty → clean）。"""
        record = self._sessions.get(app_id)
        if record is None:
            return {"ok": False, "error": f"會話未開啟：{app_id}"}
        record.state = STATE_OPEN
        record.dirty = False
        self._log("save", app_id, "ok", f"已保存（op_count={record.op_count}）", "auto")
        return {"ok": True, "session": record.snapshot()}

    async def close_app(self, app_id: str, confirm: bool = False) -> Dict[str, Any]:
        """關閉會話；有未保存變更時需 confirm=True。"""
        record = self._sessions.get(app_id)
        if record is None:
            return {"ok": False, "error": f"會話未開啟：{app_id}"}
        if record.dirty and not confirm:
            self._log("close", app_id, "pending", "有未保存變更，關閉待確認", "auto")
            return {
                "ok": False,
                "status": "pending_confirmation",
                "confirm_required": True,
                "message": f"會話 {app_id} 有未保存變更；confirm=True 放棄並關閉，或先 save",
            }
        record.state = STATE_CLOSING
        del self._sessions[app_id]
        self._log("close", app_id, "ok", f"已關閉（op_count={record.op_count}）", "auto")
        return {"ok": True, "closed": app_id, "op_count": record.op_count}

    # ---------- 學習日誌 ----------

    def _log(self, action: str, target: str, outcome: str, lesson: str, source: str) -> None:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "target": target,
            "outcome": outcome,
            "lesson": lesson,
            "source": source,
        }
        try:
            self._log_path.parent.mkdir(parents=True, exist_ok=True)
            with self._log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as exc:
            logger.warning("學習日誌寫入失敗：%s", exc)

    def learning_tail(self, limit: int = 20) -> List[Dict[str, Any]]:
        """讀回最近 N 筆學習記錄（供 AI 自省／學習器收斂）。"""
        if not self._log_path.exists():
            return []
        lines = self._log_path.read_text(encoding="utf-8").splitlines()
        out: List[Dict[str, Any]] = []
        for line in lines[-limit:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out
