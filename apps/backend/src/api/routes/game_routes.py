"""
Game API routes — REST endpoints wrapping the headless GameEngine.

Unified-frontend integration: exposes the game as switchable components so the
web-live2d-viewer shell (and any other client) can drive a game session without
a terminal. The CLI (apps/game-rpg/run_game.py) and this REST surface share the
same data source (apps/game-rpg/data/game_cards.json); the engine remains
headless and never touches the CLI.

Endpoints:
  GET    /game/status                     → Engine availability + card count
  GET    /game/worlds                     → Selectable worlds
  GET    /game/characters                 → Playable characters
  GET    /game/cards                      → Compact card catalog (type/limit filter)
  GET    /game/axes                       → Axis systems (4 lineages × 3 axes)
  GET    /game/validate                   → Deterministic rule report over full deck
  POST   /game/sessions                   → Start new game session
  GET    /game/sessions/{sid}             → Current state
  POST   /game/sessions/{sid}/action      → Advance with text input
  DELETE /game/sessions/{sid}             → End session

ANGELA-MATRIX: [L4-L5] [αβγδ] [A] [L3]
"""

import importlib
import logging
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/game", tags=["Game"])

# ---------------------------------------------------------------------------
# Engine + session management
# ---------------------------------------------------------------------------

_GAME_ROOT = (
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "apps" / "game-rpg"
)
_AXIS_PATH = _GAME_ROOT / "axis_system.py"

_ENGINE = None
_ENGINE_LOCK = threading.Lock()
_SESSIONS: Dict[str, Any] = {}
_SESSION_LOCK = threading.Lock()
_SESSION_MAX = 64

_AXIS_ENGINE: Optional[Dict[str, Any]] = None
_AXIS_LOCK = threading.Lock()


def _get_engine():
    """Lazily build (and cache) the shared GameEngine."""
    global _ENGINE
    if _ENGINE is None:
        with _ENGINE_LOCK:
            if _ENGINE is None:
                from game.engine import GameEngine

                _ENGINE = GameEngine()
    return _ENGINE


def _load_axis_system():
    """Load axis data from apps/game-rpg/axis_system.py (config-driven, same
    cross-app data dependency the engine already uses for game_cards.json)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_game_axis_system", _AXIS_PATH)
    if spec is None or spec.loader is None:
        return {}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {
        "axes": getattr(module, "AXIS_SYSTEMS", {}),
        "dimensions": list(getattr(module, "DIMENSIONS", ())),
        "default_lineage": getattr(module, "DEFAULT_LINEAGE", "其他"),
    }


def _get_axis_engine() -> Dict[str, Any]:
    """§6.4 萬物皆軸引擎共享例項（只讀狀態來源）。

    game-rpg 根路徑 bootstrap 同 tests/conftest.py 先例（已存在則跳過）；
    僅建 MasterClock+story 群組（真檔 351 卡→FSM 狀態域），**不啟動**
    任何 tick 迴圈——端點只讀、無副作用。
    """
    global _AXIS_ENGINE
    if _AXIS_ENGINE is None:
        with _AXIS_LOCK:
            if _AXIS_ENGINE is None:
                root = str(_GAME_ROOT)
                if root not in sys.path:
                    sys.path.insert(0, root)
                # 動態載入（Any 綁定）：engine 套件在 game-rpg 根、
                # 不在後端 import 路徑——同 M5/M6 動態解析先例，不靜態綁
                engine_mod: Any = importlib.import_module("engine")
                content_mod: Any = importlib.import_module("engine.content")

                group = content_mod.story_group()
                clock = engine_mod.MasterClock(master_hz=60.0)
                clock.register_group(group)
                _AXIS_ENGINE = {"clock": clock, "groups": [group]}
    return _AXIS_ENGINE


def _axis_group_to_dict(group) -> dict:
    """AxisGroup → JSON-safe 狀態表（fsm 給狀態數、數值軸給 step）。"""
    axes_out: Dict[str, Any] = {}
    for name, spec in group.axes.items():
        if spec.kind == "fsm":
            axes_out[name] = {"kind": spec.kind, "states": len(spec.states)}
        else:
            axes_out[name] = {"kind": spec.kind, "step": spec.step}
    return {
        "name": group.name,
        "tick_rate": group.tick_rate,
        "time_scale": group.time_scale,
        "axes": axes_out,
        "signals": list(group.contract.provide_names()),
    }


def _state_to_dict(state) -> dict:
    """Serialize a GameState dataclass tree into JSON-safe primitives."""
    pc = state.pc
    scene = state.scene
    return {
        "turn": state.turn,
        "quit": bool(state.quit),
        "game_over": pc.hp <= 0 or state.turn >= 50,
        "pc": {
            "card_id": pc.card_id,
            "name": pc.name,
            "description": pc.description,
            "hp": pc.hp,
            "max_hp": pc.max_hp,
            "spirit": pc.spirit,
            "max_spirit": pc.max_spirit,
            "skill": pc.skill,
            "max_skill": pc.max_skill,
            "inventory": list(pc.inventory),
            "equipment": dict(pc.equipment),
        },
        "scene": {
            "card_id": scene.card_id,
            "name": scene.name,
            "description": scene.description,
            "spirit_density": scene.spirit_density,
            "temperature": scene.temperature,
            "characters": list(scene.characters),
        },
        "messages": [
            {"speaker": m.speaker, "text": m.text, "kind": m.kind} for m in state.messages
        ],
        "choices": list(state.choices),
    }


def _session_id() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Read-only endpoints
# ---------------------------------------------------------------------------


@router.get("/status")
def game_status() -> dict:
    """Engine availability + card count."""
    try:
        engine = _get_engine()
        return {"available": True, "total_cards": len(engine.cards), "version": "1.6"}
    except Exception as err:
        logger.warning("Game engine unavailable: %s", err, exc_info=True)
        return {"available": False, "total_cards": 0}


@router.get("/engine/status")
def game_engine_status() -> dict:
    """§6.4：萬物皆軸引擎只讀狀態（master tick/組清單/軸域），不啟動迴圈。"""
    try:
        core = _get_axis_engine()
        clock = core["clock"]
        return {
            "engine": "axis-v1",
            "available": True,
            "master_hz": clock.master_hz,
            "master_ticks": clock.master_ticks,
            "groups": [_axis_group_to_dict(g) for g in core["groups"]],
        }
    except Exception as err:
        logger.warning("Axis engine unavailable: %s", err, exc_info=True)
        return {
            "engine": "axis-v1",
            "available": False,
            "master_ticks": 0,
            "groups": [],
        }


@router.get("/worlds")
def game_worlds() -> dict:
    try:
        return {"worlds": _get_engine().get_worlds()}
    except Exception as err:
        logger.warning("Game worlds unavailable: %s", err, exc_info=True)
        raise HTTPException(status_code=503, detail=f"Game engine unavailable: {err}")


@router.get("/characters")
def game_characters() -> dict:
    try:
        return {"characters": _get_engine().get_characters()}
    except Exception as err:
        logger.warning("Game characters unavailable: %s", err, exc_info=True)
        raise HTTPException(status_code=503, detail=f"Game engine unavailable: {err}")


@router.get("/cards")
def game_cards(card_type: Optional[str] = None, limit: int = 200) -> dict:
    """Compact card catalog. Optional card_type filter + limit (default 200)."""
    try:
        engine = _get_engine()
    except Exception as err:
        logger.warning("Game cards unavailable: %s", err, exc_info=True)
        raise HTTPException(status_code=503, detail=f"Game engine unavailable: {err}")

    cards: List[dict] = []
    for c in engine.cards:
        if card_type and c.get("card_type") != card_type:
            continue
        tokens = c.get("tokens", [])
        cards.append(
            {
                "card_id": c.get("card_id"),
                "card_type": c.get("card_type"),
                "name": c.get("name", c.get("card_id")),
                "description": (c.get("description") or "")[:200],
                "abilities": len(c.get("abilities", [])),
                "token_count": len(tokens),
                "has_time_data": bool(c.get("time_data")),
            }
        )
        if len(cards) >= limit:
            break
    return {"cards": cards, "total": len(cards), "card_type": card_type}


@router.get("/axes")
def game_axes() -> dict:
    try:
        return dict(_load_axis_system())
    except Exception as err:
        logger.warning("Game axes unavailable: %s", err, exc_info=True)
        raise HTTPException(status_code=503, detail=f"Axis system unavailable: {err}")


@router.get("/validate")
def game_validate() -> dict:
    """數理化/結構一致性驗證：跑完整卡片集確定性規則（卡片數以
    report.total_cards 動態回傳），回報硬錯誤（errors）與軟警告（warnings）。"""
    try:
        from game.card_validator import load_report

        report = load_report()
    except Exception as err:
        logger.warning("Game card validation unavailable: %s", err, exc_info=True)
        raise HTTPException(status_code=503, detail=f"Card validation unavailable: {err}")
    return {
        "ok": report.ok,
        "total_cards": report.total_cards,
        "errors": report.errors,
        "warnings": report.warnings,
        "issues": [
            {"card_id": i.card_id, "rule": i.rule, "severity": i.severity, "message": i.message}
            for i in report.issues
        ],
    }


# ---------------------------------------------------------------------------
# Session endpoints
# ---------------------------------------------------------------------------


@router.post("/sessions")
def game_session_new(
    pc_card_id: str = Body("CC-01", embed=True),
    scene_card_id: str = Body("S15", embed=True),
) -> dict:
    """Start a new session and return its initial state."""
    with _SESSION_LOCK:
        if len(_SESSIONS) >= _SESSION_MAX:
            # Evict oldest (dict preserves insertion order) to bound memory.
            _SESSIONS.pop(next(iter(_SESSIONS)))
    sid = _session_id()
    try:
        engine = _get_engine()
        state = engine.new_game(pc_card_id=pc_card_id, scene_card_id=scene_card_id)
    except Exception as err:
        logger.warning("Game session init failed: %s", err, exc_info=True)
        raise HTTPException(status_code=400, detail=f"Cannot start game: {err}")
    with _SESSION_LOCK:
        _SESSIONS[sid] = engine
    return {"session_id": sid, "state": _state_to_dict(state)}


@router.get("/sessions/{sid}")
def game_session_state(sid: str) -> dict:
    engine = _SESSIONS.get(sid)
    if engine is None:
        raise HTTPException(status_code=404, detail=f"Session {sid} not found")
    try:
        return {"session_id": sid, "state": _state_to_dict(engine.state)}
    except RuntimeError as err:
        raise HTTPException(status_code=409, detail=str(err))


@router.post("/sessions/{sid}/action")
def game_session_action(sid: str, text: str = Body("", embed=True)) -> dict:
    engine = _SESSIONS.get(sid)
    if engine is None:
        raise HTTPException(status_code=404, detail=f"Session {sid} not found")
    try:
        state = engine.process_input(text or "")
    except Exception as err:
        logger.warning("Game action failed: %s", err, exc_info=True)
        raise HTTPException(status_code=400, detail=str(err))
    return {"session_id": sid, "state": _state_to_dict(state)}


@router.delete("/sessions/{sid}")
def game_session_end(sid: str) -> dict:
    with _SESSION_LOCK:
        if _SESSIONS.pop(sid, None) is None:
            raise HTTPException(status_code=404, detail=f"Session {sid} not found")
    return {"session_id": sid, "status": "ended"}
