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
  GET    /game/engine/status              → Axis engine + M8 runner status (read-only)
  POST   /game/engine/start               → Start resident tick loop (idempotent)
  POST   /game/engine/stop                → Stop resident tick loop (idempotent)
  GET    /game/engine/snapshot            → Runner snapshot for poll consumers
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
_AXIS_RUNNER: Optional[Any] = None
_AXIS_RUNNER_LOCK = threading.Lock()


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


def _story_publish_handler(seed: Dict[str, Any]):
    """story 群組運行期心跳：首發播種焦點卡，其後每 fire 重播（M8）。

    story 契約 provides card_type/story_role——執行器跑起來後，其他群組
    與輪詢端經 snapshot.signals["story"] 讀到當前劇情焦點。seed 為 M5
    card_to_values 的真卡軸值（首卡），非空即覆蓋。
    """

    def handler(ctx) -> None:
        card_type = ctx.read("story.card_type")
        story_role = ctx.read("story.story_role")
        ctx.emit("card_type", card_type if isinstance(card_type, str) else str(seed["card_type"]))
        ctx.emit(
            "story_role", story_role if isinstance(story_role, str) else str(seed["story_role"])
        )

    return handler


def _get_axis_runner() -> Any:
    """§6.4 後續 M8：常駐 tick 迴圈共享例項（story 群組+世界線流速外包）。

    建構即註冊 story 群組（351 真檔卡→FSM 狀態域）＋首卡播種 handler，
    startup() 驗契約；**不自動啟動**執行緒——start 由
    POST /game/engine/start 明確觸發。
    """
    global _AXIS_RUNNER
    if _AXIS_RUNNER is None:
        with _AXIS_RUNNER_LOCK:
            if _AXIS_RUNNER is None:
                root = str(_GAME_ROOT)
                if root not in sys.path:
                    sys.path.insert(0, root)
                engine_mod: Any = importlib.import_module("engine")
                content_mod: Any = importlib.import_module("engine.content")
                world_clock_mod: Any = importlib.import_module("world_clock")

                cards = content_mod.load_cards()
                seed = content_mod.card_to_values(cards[0])
                runner = engine_mod.EngineRunner(
                    master_hz=60.0,
                    time_flow_source=world_clock_mod.get_time_flow_ratio,
                )
                runner.register(content_mod.story_group(cards), _story_publish_handler(seed))
                runner.startup()
                _AXIS_RUNNER = runner
    return _AXIS_RUNNER


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


def _runner_status_safe() -> dict:
    """status 端點的 runner 塊：建構失敗降級不拖垮整個 status（同 available:false 慣例）。"""
    try:
        snap = _get_axis_runner().snapshot()
        return {
            "running": snap["running"],
            "master_ticks": snap["master_ticks"],
            "groups": sorted(snap["groups"]),
        }
    except Exception as err:
        logger.warning("Axis runner status unavailable: %s", err, exc_info=True)
        return {"running": False, "master_ticks": 0, "groups": []}


@router.get("/engine/status")
def game_engine_status() -> dict:
    """§6.4：萬物皆軸引擎只讀狀態（master tick/組清單/軸域/M8 runner 塊），不啟動迴圈。"""
    try:
        core = _get_axis_engine()
        clock = core["clock"]
        return {
            "engine": "axis-v1",
            "available": True,
            "master_hz": clock.master_hz,
            "master_ticks": clock.master_ticks,
            "groups": [_axis_group_to_dict(g) for g in core["groups"]],
            "runner": _runner_status_safe(),
        }
    except Exception as err:
        logger.warning("Axis engine unavailable: %s", err, exc_info=True)
        return {
            "engine": "axis-v1",
            "available": False,
            "master_ticks": 0,
            "groups": [],
            "runner": _runner_status_safe(),
        }


# ---------------------------------------------------------------------------
# M8: 常駐 tick 迴圈（§6.4「生產 tick 迴圈」遠期項；pixel-angela 輪詢消費）
# ---------------------------------------------------------------------------


@router.post("/engine/start")
def game_engine_start() -> dict:
    """啟動常駐 tick 迴圈（冪等）；story 群組心跳即時播種。"""
    try:
        snap = _get_axis_runner().start()
        return {"engine": "axis-v1", "available": True, **snap}
    except Exception as err:
        logger.warning("Axis runner start failed: %s", err, exc_info=True)
        raise HTTPException(status_code=503, detail=f"Axis runner unavailable: {err}")


@router.post("/engine/stop")
def game_engine_stop() -> dict:
    """停止常駐 tick 迴圈（冪等）；快照 master_ticks 保留最後推進數。"""
    try:
        snap = _get_axis_runner().stop()
        return {"engine": "axis-v1", "available": True, **snap}
    except Exception as err:
        logger.warning("Axis runner stop failed: %s", err, exc_info=True)
        raise HTTPException(status_code=503, detail=f"Axis runner unavailable: {err}")


@router.get("/engine/snapshot")
def game_engine_snapshot() -> dict:
    """執行器唯讀快照（running/master_ticks/組 fire/訊號表）；不啟動執行緒。"""
    try:
        snap = _get_axis_runner().snapshot()
        return {"engine": "axis-v1", "available": True, **snap}
    except Exception as err:
        logger.warning("Axis runner snapshot unavailable: %s", err, exc_info=True)
        return {
            "engine": "axis-v1",
            "available": False,
            "running": False,
            "master_ticks": 0,
            "groups": {},
            "signals": {},
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
