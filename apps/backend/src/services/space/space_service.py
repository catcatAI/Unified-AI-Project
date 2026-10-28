# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3]
# =============================================================================
"""Space service — the authoritative stage state shared by every viewer.

The browser stage (apps/space-studio) can run alone; when a backend is up it
subscribes here instead, and the service is what makes "the same room" mean the
same thing on two screens.

Deliberately small: actors, poses, speech bubbles, and a revision counter.
No tick loop — positions are set, not simulated server-side, because the
renderer owns interpolation and the service never needs to know about frames.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_ROOM_ID = "studio_a"
DEFAULT_SPEECH_TTL_MS = 4000
WARDROBE_SLOTS = ("top", "bottom", "shoes", "accessory")
_HEX_TINT = re.compile(r"^#[0-9a-fA-F]{6}$")

ActorDict = Dict[str, Any]


class SpaceService:
    """In-memory rooms + actors, with an injectable clock for expiry tests."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._rooms: Dict[str, Dict[str, Any]] = {}
        self._actors: Dict[str, ActorDict] = {}
        self._rev = 0

    # ------------------------------------------------------------------
    # rooms
    # ------------------------------------------------------------------
    def load_room(self, room: Dict[str, Any]) -> Dict[str, Any]:
        room_id = str(room.get("room_id") or "").strip()
        if not room_id:
            raise ValueError("room needs a room_id")
        self._rooms[room_id] = dict(room)
        self._touch()
        return self._rooms[room_id]

    @property
    def revision(self) -> int:
        return self._rev

    # ------------------------------------------------------------------
    # actors
    # ------------------------------------------------------------------
    def spawn(self, actor: Dict[str, Any]) -> Dict[str, Any]:
        actor_id = str(actor.get("actor_id") or actor.get("role_id") or "").strip()
        if not actor_id:
            raise ValueError("actor needs an actor_id or role_id")
        if actor_id in self._actors:
            raise ValueError(f"actor already on stage: {actor_id}")

        stored: ActorDict = {
            "actor_id": actor_id,
            "role_id": str(actor.get("role_id") or actor_id),
            "avatar_id": actor.get("avatar_id", "angela_base"),
            "position": list(actor.get("position") or [8.0, 0.0]),
            "facing": float(actor.get("facing", 0.0)),
            "expression": actor.get("expression", "neutral"),
            "motion": actor.get("motion"),
            "speech": None,
            "visible_to": actor.get("visible_to"),
            # Wardrobe lives on the actor so the backend can change it too
            # (S2: the AI decides an outfit, the stage renders it).
            "outfit": dict(actor.get("outfit") or {}),
            "outfit_rev": 0,
        }
        self._actors[actor_id] = stored
        self._touch()
        return stored

    def despawn(self, actor_id: str) -> bool:
        removed = self._actors.pop(actor_id, None) is not None
        if removed:
            self._touch()
        return removed

    def get(self, actor_id: str) -> ActorDict:
        actor = self._actors.get(actor_id)
        if actor is None:
            raise ValueError(f"unknown actor: {actor_id}")
        return actor

    # ------------------------------------------------------------------
    # actions
    # ------------------------------------------------------------------
    def move(self, actor_id: str, position: List[float]) -> ActorDict:
        actor = self.get(actor_id)
        x, y = float(position[0]), float(position[1])
        actor["position"] = [x, y]
        self._touch()
        return actor

    def face(self, actor_id: str, facing: float) -> ActorDict:
        actor = self.get(actor_id)
        actor["facing"] = float(facing)
        self._touch()
        return actor

    def play(self, actor_id: str, motion: Optional[str]) -> ActorDict:
        actor = self.get(actor_id)
        actor["motion"] = motion
        self._touch()
        return actor

    def express(self, actor_id: str, expression: str) -> ActorDict:
        actor = self.get(actor_id)
        actor["expression"] = str(expression)
        self._touch()
        return actor

    def update_avatar(
        self, actor_id: str, slot: str, item: str, tint: Optional[str] = None
    ) -> ActorDict:
        """Change one wardrobe slot (the tool a role may call).

        Values are validated here, not in the renderer: an invalid tint must be
        rejected at the seam, otherwise every viewer would have to defend itself.
        """
        if slot not in WARDROBE_SLOTS:
            raise ValueError(f"unknown wardrobe slot: {slot}")
        if not item:
            raise ValueError("update_avatar needs an item id")
        if tint is not None and not _HEX_TINT.match(str(tint)):
            raise ValueError(f"tint must be #rrggbb, got {tint}")
        actor = self.get(actor_id)
        outfit = dict(actor.get("outfit") or {})
        current = dict(outfit.get(slot) or {})
        current.update({"item": str(item)})
        if tint is not None:
            current["tint"] = str(tint)
        outfit[slot] = current
        actor["outfit"] = outfit
        actor["outfit_rev"] = int(actor.get("outfit_rev", 0)) + 1
        self._touch()
        return actor

    def say(self, actor_id: str, text: str, ttl_ms: int = DEFAULT_SPEECH_TTL_MS) -> ActorDict:
        spoken = str(text or "").strip()
        if not spoken:
            raise ValueError("say needs non-empty text")
        actor = self.get(actor_id)
        actor["speech"] = {
            "text": spoken,
            "expires_at_ms": self._clock() * 1000.0 + float(ttl_ms),
        }
        self._touch()
        return actor

    def apply(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Apply one client action and return the new snapshot."""
        kind = str(action.get("type") or "").strip()
        actor_id = str(action.get("actor_id") or "").strip()

        if kind == "spawn":
            self.spawn(action)
        elif kind == "despawn":
            self.despawn(actor_id)
        elif kind == "move":
            self.move(actor_id, action.get("position") or [8.0, 0.0])
        elif kind == "face":
            self.face(actor_id, action.get("facing", 0.0))
        elif kind == "play":
            self.play(actor_id, action.get("motion"))
        elif kind == "express":
            self.express(actor_id, action.get("expression", "neutral"))
        elif kind == "wardrobe":
            self.update_avatar(
                actor_id,
                str(action.get("slot") or ""),
                str(action.get("item") or ""),
                action.get("tint"),
            )
        elif kind == "say":
            self.say(
                actor_id, action.get("text", ""), int(action.get("ttl_ms", DEFAULT_SPEECH_TTL_MS))
            )
        else:
            raise ValueError(f"unknown space action: {kind or '<empty>'}")
        return self.snapshot()

    # ------------------------------------------------------------------
    # snapshots
    # ------------------------------------------------------------------
    def _live_speech(self, actor: ActorDict, now_ms: float) -> Optional[Dict[str, Any]]:
        speech = actor.get("speech")
        if not speech:
            return None
        if float(speech.get("expires_at_ms", 0.0)) <= now_ms:
            actor["speech"] = None
            return None
        return {"text": speech["text"]}

    def snapshot(self, room_id: Optional[str] = None) -> Dict[str, Any]:
        now_ms = self._clock() * 1000.0
        actors: List[Dict[str, Any]] = []
        for actor in self._actors.values():
            rendered = dict(actor)
            rendered["speech"] = self._live_speech(actor, now_ms)
            actors.append(rendered)
        return {
            "type": "space.snapshot",
            "rev": self._rev,
            "data": {
                "room_id": room_id or next(iter(self._rooms), DEFAULT_ROOM_ID),
                "actors": actors,
            },
        }

    def _touch(self) -> None:
        self._rev += 1


_service: Optional[SpaceService] = None


def stage_roster_path() -> Path:
    """Where the stage roster lives (repo ``space/roles.json`` by default)."""
    override = os.environ.get("ANGELA_SPACE_ROSTER")
    if override:
        return Path(override).expanduser()
    return Path(__file__).resolve().parents[5] / "space" / "roles.json"


def seed_default_stage(service: SpaceService) -> SpaceService:
    """Put the roster on stage when the service is still empty.

    Without this a freshly started backend broadcasts an empty room and the
    browser (which syncs to the snapshot) would wipe the stage it just built.
    Set ``SPACE_SEED_ROLES=0`` to run an empty stage on purpose.
    """
    if os.environ.get("SPACE_SEED_ROLES", "1") == "0":
        return service
    if service.snapshot()["data"]["actors"]:
        return service

    roster = stage_roster_path()
    if roster.exists():
        try:
            data = json.loads(roster.read_text(encoding="utf-8"))
            for entry in data.get("actors", []):
                service.spawn(
                    {
                        "role_id": entry["role_id"],
                        "avatar_id": entry.get("avatar_id", "angela_base"),
                        "position": entry.get("position", [8.0, 0.0]),
                        "visible_to": entry.get("visible_to"),
                    }
                )
            return service
        except Exception as exc:  # noqa: BLE001 - an empty stage beats a dead server
            logger.warning("Space roster %s unusable: %s", roster, exc)

    try:
        from ai.roleplay.runtime import load_roles

        for index, role in enumerate(load_roles()):
            service.spawn(
                {
                    "role_id": role.role_id,
                    "position": [5.5 + 2.5 * index, 0.0],
                }
            )
    except Exception as exc:  # noqa: BLE001 - an empty stage beats a dead server
        logger.warning("Space stage seed skipped: %s", exc)
    return service


def get_space_service() -> SpaceService:
    global _service
    if _service is None:
        _service = seed_default_stage(SpaceService())
    return _service


def set_space_service(service: "SpaceService") -> None:
    """Swap the singleton (tests, and a future per-room registry)."""
    global _service
    _service = service


def reset_space_service() -> None:
    """Test/reload seam: drop the singleton and every actor on stage."""
    global _service
    _service = None
