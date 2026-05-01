"""
Fantasy DM & Alchemy Agent
Responsible for Dungeon Master narration, Alchemy logic, and Fantasy RPG mechanics.
Migrated from 'Witch's Alchemy Chronicle' and 'TRPG Game' frontend logic.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class FantasyDMAgent(BaseAgent):
    def __init__(self, agent_id: str = "fantasy_dm", agent_name: str = "Fantasy DM Agent"):
        super().__init__(agent_id=agent_id, agent_name=agent_name)
        self.capabilities = ["alchemy_brewing", "rpg_narration", "codex_lookup"]
        self.codex_path = "apps/backend/data/trpg/ai-trpg-codex.json"
        self._codex_cache = None

    def _load_codex(self):
        if self._codex_cache is None:
            try:
                import os
                # Look for codex relative to project root
                full_path = os.path.abspath(self.codex_path)
                if os.path.exists(full_path):
                    with open(full_path, "r", encoding="utf-8") as f:
                        self._codex_cache = json.load(f)
                else:
                    logger.warning(f"TRPG Codex not found at {full_path}")
                    self._codex_cache = {}
            except Exception as e:
                logger.error(f"Failed to load TRPG Codex: {e}")
                self._codex_cache = {}
        return self._codex_cache

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action = task.get("action")
        params = task.get("parameters", {})

        if action == "alchemy_brewing":
            return await self._handle_alchemy(params)
        elif action == "rpg_narration":
            return await self._handle_narration(params)
        elif action == "codex_lookup":
            return self._handle_codex_lookup(params)
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    async def _handle_alchemy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        item1 = params.get("item1", {})
        item2 = params.get("item2", {})
        
        # Meta-Prompt for Alchemy Logic
        prompt = f"""
        Role: Alchemy System for 'Witch's Alchemy Chronicle'.
        Items: 1. {item1.get('name')} ({item1.get('description')}), 2. {item2.get('name')} ({item2.get('description')})
        Action: Determine the brewing result.
        Output: JSON with 'success', 'message', and 'item' if successful.
        """
        # Note: In real implementation, this calls self.llm_interface.generate_json
        return {
            "status": "success",
            "payload": {
                "success": True,
                "message": f"Successfully combined {item1.get('name')} and {item2.get('name')}.",
                "item": {"id": "mystery_potion", "name": "Mystery Potion", "description": "A shimmering liquid."}
            }
        }

    async def _handle_narration(self, params: Dict[str, Any]) -> Dict[str, Any]:
        location = params.get("location_name", "Unknown")
        description = params.get("base_description", "")
        
        return {
            "status": "success",
            "payload": {
                "narration": f"The air in {location} is thick with magical residue. {description}"
            }
        }

    def _handle_codex_lookup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "").lower()
        codex = self._load_codex()
        
        # Search for characters, items, or locations
        results = []
        for cat in ["characters", "items", "locations"]:
            if cat in codex:
                for key, val in codex[cat].items():
                    if query in key.lower() or query in str(val).lower():
                        results.append({"category": cat, "id": key, "data": val})
        
        return {"status": "success", "results": results[:5]}
