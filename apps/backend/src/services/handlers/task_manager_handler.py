"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
TaskManagerHandler — manages a simple JSON-backed task list.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_TASKS_DIR = Path.home() / ".angela" / "tasks"
_TASKS_FILE = _TASKS_DIR / "tasks.json"


def _load_tasks() -> List[Dict[str, Any]]:
    if _TASKS_FILE.exists():
        try:
            data = json.loads(_TASKS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            return []
        except (json.JSONDecodeError, ValueError):
            backup = _TASKS_DIR / "tasks.json.bak"
            if backup.exists():
                try:
                    return json.loads(backup.read_text(encoding="utf-8"))
                except Exception:
                    pass
            return []
    return []


def _save_tasks(tasks: List[Dict[str, Any]]) -> None:
    _TASKS_DIR.mkdir(parents=True, exist_ok=True)
    if _TASKS_FILE.exists():
        try:
            import shutil
            shutil.copy2(_TASKS_FILE, _TASKS_DIR / "tasks.json.bak")
        except Exception:
            pass
    _TASKS_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


class TaskManagerHandler:
    """Manages tasks: create, list, complete, delete, update."""

    async def handle(self, text: str, intent: str = "task") -> str:
        action, payload = self._parse(text)
        if action == "create":
            return self._create(payload)
        elif action == "list":
            return self._list()
        elif action == "complete":
            return self._complete(payload)
        elif action == "delete":
            return self._delete(payload)
        elif action == "update":
            return self._update(payload)
        else:
            return "（任務管理）可用操作：建立任務、任務列表、完成任務、刪除任務。"

    def _parse(self, text: str) -> tuple:
        import re
        text = text.strip()
        if any(k in text for k in ["建立任務", "新增任務", "添加任務", "add task", "create task"]):
            m = re.search(r"[：:]\s*(.+)", text)
            title = m.group(1).strip() if m else re.sub(r"建立任務|新增任務|添加任務|add task|create task", "", text, flags=re.IGNORECASE).strip()
            return "create", {"title": title}
        if any(k in text for k in ["任務列表", "待辦事項", "todo list", "task list", "list tasks"]):
            return "list", {}
        if any(k in text for k in ["完成任務", "完成待辦", "complete task"]):
            m = re.search(r"[#＃]?\s*(\d+)", text)
            return "complete", {"id": int(m.group(1))} if m else ("complete", {"title": text})
        if any(k in text for k in ["刪除任務", "移除任務", "delete task", "remove task"]):
            m = re.search(r"[#＃]?\s*(\d+)", text)
            return "delete", {"id": int(m.group(1))} if m else ("delete", {"title": text})
        if any(k in text for k in ["更新任務", "修改任務", "update task"]):
            m = re.search(r"[#＃]?\s*(\d+)\s*[：:]\s*(.+)", text)
            if m:
                return "update", {"id": int(m.group(1)), "title": m.group(2).strip()}
            return "update", {"title": text}
        return "create", {"title": text}

    def _create(self, payload: Dict[str, Any]) -> str:
        title = payload.get("title", "").strip()
        if not title:
            return "（任務管理）請提供任務標題。"
        tasks = _load_tasks()
        task_id = max((t.get("id", 0) for t in tasks), default=0) + 1
        tasks.append({
            "id": task_id,
            "title": title,
            "status": "pending",
            "created_at": time.time(),
        })
        _save_tasks(tasks)
        return f"（任務管理）已建立任務 #{task_id}：{title}"

    def _list(self) -> str:
        tasks = _load_tasks()
        pending = [t for t in tasks if t.get("status") == "pending"]
        done = [t for t in tasks if t.get("status") == "completed"]
        if not tasks:
            return "（任務管理）目前沒有任何任務。"
        lines = ["（任務管理）任務列表："]
        if pending:
            lines.append("  待完成：")
            for t in pending[:20]:
                lines.append(f"    #{t['id']} {t['title']}")
        if done:
            lines.append("  已完成：")
            for t in done[-5:]:
                lines.append(f"    #{t['id']} {t['title']} ✓")
        return "\n".join(lines)

    def _complete(self, payload: Dict[str, Any]) -> str:
        tasks = _load_tasks()
        task_id = payload.get("id")
        title = payload.get("title", "")
        for t in tasks:
            if task_id and t.get("id") == task_id:
                t["status"] = "completed"
                _save_tasks(tasks)
                return f"（任務管理）已標記任務 #{task_id} 為完成：{t['title']}"
            if title and t.get("title") == title and t.get("status") == "pending":
                t["status"] = "completed"
                _save_tasks(tasks)
                return f"（任務管理）已標記任務 #{t['id']} 為完成：{title}"
        return f"（任務管理）找不到對應的任務。"

    def _delete(self, payload: Dict[str, Any]) -> str:
        tasks = _load_tasks()
        task_id = payload.get("id")
        title = payload.get("title", "")
        original_len = len(tasks)
        tasks = [t for t in tasks if not (task_id and t.get("id") == task_id) and not (title and t.get("title") == title)]
        if len(tasks) == original_len:
            return f"（任務管理）找不到對應的任務。"
        _save_tasks(tasks)
        return f"（任務管理）已刪除任務。"

    def _update(self, payload: Dict[str, Any]) -> str:
        tasks = _load_tasks()
        task_id = payload.get("id")
        new_title = payload.get("title", "")
        for t in tasks:
            if task_id and t.get("id") == task_id:
                old_title = t["title"]
                t["title"] = new_title
                _save_tasks(tasks)
                return f"（任務管理）已更新任務 #{task_id}：{old_title} → {new_title}"
            if new_title and t.get("title") != new_title and t.get("status") == "pending":
                old_title = t["title"]
                t["title"] = new_title
                _save_tasks(tasks)
                return f"（任務管理）已更新任務 #{t['id']}：{old_title} → {new_title}"
        return f"（任務管理）找不到對應的任務。"


__all__ = ["TaskManagerHandler"]
