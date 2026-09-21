"""
Game Memory Bridge - HAM 記憶系統的遊戲適配層

功能：
- 經驗存儲與檢索 (情節記憶)
- 語義記憶：配方、方塊屬性、生物特性
- 空間記憶：資源點、基地位置、危險區
- 程序記憶：技能序列、製作鏈
"""

import asyncio
import json
import logging
import math
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    EPISODIC = "episodic"  # 具體經驗：時間、地點、事件
    SEMANTIC = "semantic"  # 知識：配方、屬性、規則
    SPATIAL = "spatial"  # 空間：位置、路徑、地標
    PROCEDURAL = "procedural"  # 程序：技能序列、製作鏈


@dataclass
class GameExperience:
    """遊戲經驗記錄"""

    exp_id: str
    memory_type: MemoryType
    timestamp: float
    position: Tuple[float, float, float]
    action: str
    context: Dict[str, Any]  # 當時狀態
    outcome: Dict[str, Any]  # 結果
    reward: float  # 獎勵值 (-1 到 1)
    tags: List[str] = field(default_factory=list)  # 搜索標籤


@dataclass
class SpatialMemory:
    """空間記憶節點"""

    location_id: str
    position: Tuple[float, float, float]
    node_type: str  # "resource", "base", "danger", "landmark", "spawn"
    resources: Dict[str, int]  # 資源分布
    last_seen: float = 0.0  # 最後「看到」（observe_world 刷新）
    last_visited: float = 0.0  # 最後「到訪」（agent 實際到場，好奇心用）
    visit_count: int = 0
    danger_level: float = 0.0
    notes: str = ""

    @property
    def staleness(self) -> float:
        """探索價值：看過但久未親訪的點最值得重訪。"""
        if self.last_visited:
            return min(time.time() - self.last_visited, time.time() - self.last_seen)
        return time.time() - self.last_seen


@dataclass
class RecipeMemory:
    """配方記憶"""

    recipe_id: str
    ingredients: Dict[str, int]
    result: str
    result_count: int
    station: str = "crafting_table"  # "crafting_table", "furnace", "anvil"
    unlocked: bool = True
    proficiency: float = 0.0  # 熟練度 0-1


# Minetest itemstring -> 配方短名。遊戲報的是 default:cobble，
# 配方寫的是 cobblestone；不斷層判斷（可合成嗎？做完了嗎？）全錯。
# 與 apps/luanti-mods/agent_poller/init.lua 的 ITEMS 表同源，保持同步。
ITEM_ALIASES = {
    "default:wood": "wood",
    "default:cobble": "cobblestone",
    "default:stick": "stick",
    "default:coal_lump": "coal",
    "default:pick_wood": "wooden_pickaxe",
    "default:pick_stone": "stone_pickaxe",
    "default:axe_stone": "stone_axe",
    "default:shovel_stone": "stone_shovel",
    "default:sword_stone": "stone_sword",
    "default:furnace": "furnace",
    "default:chest": "chest",
    "default:workbench": "crafting_table",
    "default:torch": "torch",
    "default:sand": "sand",
    "default:dirt": "dirt",
}


def normalize_inventory(inventory: Dict[str, Any]) -> Dict[str, int]:
    """itemstring 背包折成短名計數（未知名原樣保留）。"""
    out: Dict[str, int] = {}
    for key, val in (inventory or {}).items():
        try:
            count = int(val)
        except (TypeError, ValueError):
            continue
        short = ITEM_ALIASES.get(str(key), str(key))
        out[short] = out.get(short, 0) + count
    return out


class GameMemoryBridge:
    """
    HAM 記憶橋接器

    封裝底層 HAM 操作，提供遊戲特化的查詢介面
    """

    # 記憶體護欄（計畫風險表「記憶體洩漏」對策）：地點/經驗超出即丟最舊
    MAX_SPATIAL = 2000
    MAX_EXPERIENCES = 500

    def __init__(self, ham_manager=None):
        self._ham = ham_manager
        self._experiences: List[GameExperience] = []
        self._spatial_index: Dict[str, SpatialMemory] = {}
        self._recipes: Dict[str, RecipeMemory] = {}
        self._procedural_chains: Dict[str, List[str]] = defaultdict(list)
        self._initialized = False
        self._init_default_recipes()

    # ==================== 空間記憶持久化 ====================

    def save_spatial(self, path: str) -> bool:
        """空間記憶存 JSON（原子寫）。位置取整 1m 格，與 loc_id 口徑一致。"""
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            payload = {
                "version": 1,
                "saved_at": time.time(),
                "locations": [
                    {
                        "location_id": n.location_id,
                        "position": [
                            round(float(n.position[0]), 1),
                            round(float(n.position[1]), 1),
                            round(float(n.position[2]), 1),
                        ],
                        "node_type": n.node_type,
                        "resources": dict(n.resources),
                        "last_seen": n.last_seen,
                        "last_visited": n.last_visited,
                        "visit_count": n.visit_count,
                        "danger_level": n.danger_level,
                        "notes": n.notes,
                    }
                    for n in self._spatial_index.values()
                ],
            }
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            os.replace(tmp, path)
            return True
        except Exception as e:
            logger.error(f"save_spatial failed: {e}")
            return False

    def load_spatial(self, path: str) -> int:
        """讀回空間記憶，返回載入的地點數。檔案不存在返回 0。"""
        try:
            if not os.path.exists(path):
                return 0
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            n_loaded = 0
            for item in payload.get("locations", []):
                # 逐行容錯：單行壞資料跳過，不炸掉整份記憶
                try:
                    pos = item.get("position") or [0.0, 0.0, 0.0]
                    loc_id = str(
                        item.get("location_id") or f"{int(pos[0])}_{int(pos[1])}_{int(pos[2])}"
                    )
                    self._spatial_index[loc_id] = SpatialMemory(
                        location_id=loc_id,
                        position=(float(pos[0]), float(pos[1]), float(pos[2])),
                        node_type=str(item.get("node_type", "unknown")),
                        resources={
                            str(k): int(v) for k, v in (item.get("resources") or {}).items()
                        },
                        last_seen=float(item.get("last_seen", 0.0)),
                        last_visited=float(item.get("last_visited", 0.0)),
                        visit_count=int(item.get("visit_count", 0)),
                        danger_level=float(item.get("danger_level", 0.0)),
                        notes=str(item.get("notes", "")),
                    )
                    n_loaded += 1
                except (TypeError, ValueError, KeyError) as e:
                    logger.warning(f"load_spatial skipped bad row: {e}")
            logger.info(f"Loaded {n_loaded} spatial memories from {path}")
            return n_loaded
        except Exception as e:
            logger.error(f"load_spatial failed: {e}")
            return 0

    def _init_default_recipes(self):
        """初始化預設配方知識"""
        default_recipes = {
            "wooden_pickaxe": RecipeMemory("wooden_pickaxe", {"wood": 3}, "wooden_pickaxe", 1),
            "stone_pickaxe": RecipeMemory(
                "stone_pickaxe", {"cobblestone": 3, "stick": 2}, "stone_pickaxe", 1
            ),
            "stone_axe": RecipeMemory("stone_axe", {"cobblestone": 3, "stick": 2}, "stone_axe", 1),
            "stone_shovel": RecipeMemory(
                "stone_shovel", {"cobblestone": 1, "stick": 2}, "stone_shovel", 1
            ),
            "stone_sword": RecipeMemory(
                "stone_sword", {"cobblestone": 2, "stick": 1}, "stone_sword", 1
            ),
            "furnace": RecipeMemory("furnace", {"cobblestone": 8}, "furnace", 1),
            "chest": RecipeMemory("chest", {"wood": 8}, "chest", 1),
            "crafting_table": RecipeMemory("crafting_table", {"wood": 4}, "crafting_table", 1),
            "stick": RecipeMemory("stick", {"wood": 2}, "stick", 4),
            "torch": RecipeMemory("torch", {"stick": 1, "coal": 1}, "torch", 4),
            "iron_ingot": RecipeMemory(
                "iron_ingot", {"iron_ore": 1}, "iron_ingot", 1, station="furnace"
            ),
            "iron_pickaxe": RecipeMemory(
                "iron_pickaxe", {"iron_ingot": 3, "stick": 2}, "iron_pickaxe", 1
            ),
        }
        self._recipes.update(default_recipes)

    async def initialize(self, ham_manager):
        """初始化 HAM 連接"""
        self._ham = ham_manager
        self._initialized = True
        logger.info("GameMemoryBridge initialized")

    # ==================== 世界觀察（識別→記憶閉環） ====================

    def observe_world(
        self,
        position: Tuple[float, float, float],
        nodes: List[Dict[str, Any]],
        source: str = "scan",
        timestamp: Optional[float] = None,
    ) -> int:
        """把掃描/視線看到的節點寫進空間記憶。

        nodes 元素: {"node": "default:tree", "x":.., "y":.., "z":..}（scan）
        或 {"node": .., "dist":.., "yaw_off":..}（vision，以自身位置+朝向推回世界座標）。
        返回新發現的地點數。vision 的朝向數學由呼叫端做（這裡只收世界座標）。
        """
        ts = timestamp if timestamp is not None else time.time()
        new_spots = 0
        for n in nodes or []:
            node_name = str(n.get("node", ""))
            if not node_name or node_name == "air":
                continue
            if "x" in n and "z" in n and "y" in n:
                wpos = (float(n["x"]), float(n["y"]), float(n["z"]))
            else:
                continue
            loc_id = f"{int(wpos[0])}_{int(wpos[1])}_{int(wpos[2])}"
            spot = self._spatial_index.get(loc_id)
            if spot is None:
                if len(self._spatial_index) >= self.MAX_SPATIAL:
                    # 丟最舊的（last_seen 最小），維持上限
                    oldest = min(self._spatial_index.values(), key=lambda s: s.last_seen)
                    del self._spatial_index[oldest.location_id]
                spot = SpatialMemory(
                    location_id=loc_id,
                    position=wpos,
                    node_type="resource",
                    resources={},
                    last_seen=ts,
                )
                self._spatial_index[loc_id] = spot
                new_spots += 1
            spot.last_seen = max(spot.last_seen, ts)
            key = node_name.split(":")[-1]
            spot.resources[key] = spot.resources.get(key, 0) + 1
            if spot.notes and source not in spot.notes:
                spot.notes = f"{spot.notes},{source}"[:80]
            elif not spot.notes:
                spot.notes = source
        return new_spots

    def find_unexplored(
        self,
        position: Tuple[float, float, float],
        max_dist: float = 80.0,
        min_age_sec: float = 180.0,
    ) -> Optional[SpatialMemory]:
        """找最久沒「親訪」的已知資源點（好奇心：看過≠去過）。

        語意：observe_world 只刷新 last_seen（看到）；last_visited 只由
        agent 到場更新。看過但久未親訪 → staleness 大 → 值得走去看看。
        """
        now = time.time()
        best = None
        best_score = -1.0
        for node in self._spatial_index.values():
            if node.node_type == "danger" or node.danger_level >= 1.0:
                continue
            dist = self._distance(position, node.position)
            if dist <= 0.5 or dist > max_dist:
                continue
            # 從沒親訪過的點用 last_seen 當年齡（看過很久了還沒去過）
            age = now - node.last_visited if node.last_visited else now - node.last_seen
            if age < min_age_sec:
                continue
            # 老地方加權，但太遠扣分（可達性）
            score = age / 60.0 - dist / 40.0
            if score > best_score:
                best_score = score
                best = node
        return best

    def mark_visited(self, position: Tuple[float, float, float], radius: float = 3.0) -> int:
        """agent 實際到場：更新附近地點的 last_visited/visit_count（好奇心語意基準）。"""
        ts = time.time()
        n = 0
        for spot in self._spatial_index.values():
            if self._distance(position, spot.position) <= radius:
                spot.last_visited = ts
                spot.visit_count += 1
                n += 1
        return n

    def spatial_stats(self) -> Dict[str, Any]:
        """空間記憶統計（觀測性用）。"""
        types: Dict[str, int] = defaultdict(int)
        for n in self._spatial_index.values():
            types[n.node_type] += 1
        return {"total": len(self._spatial_index), "by_type": dict(types)}

    # ==================== 經驗存儲 ====================

    async def store_experience(self, exp: GameExperience):
        """存儲經驗到 HAM"""
        self._experiences.append(exp)
        if len(self._experiences) > self.MAX_EXPERIENCES:
            # 護欄：丟最舊，避免長時間運行記憶體洩漏
            del self._experiences[: len(self._experiences) - self.MAX_EXPERIENCES]

        # 同時更新空間/程序記憶
        if exp.memory_type == MemoryType.SPATIAL:
            await self._update_spatial(exp)
        elif exp.memory_type == MemoryType.PROCEDURAL:
            await self._update_procedural(exp)

        # 寫入 HAM (非阻塞)
        if self._ham:
            asyncio.create_task(self._write_to_ham(exp))

    async def _write_to_ham(self, exp: GameExperience):
        """寫入 HAM 後端 (真實調用 HAMMemoryManager.store_experience)"""
        try:
            await self._ham.store_experience(
                raw_data={
                    "action": exp.action,
                    "position": list(exp.position),
                    "outcome": exp.outcome,
                    "reward": exp.reward,
                },
                data_type="game_experience",
                metadata={
                    "memory_type": exp.memory_type.value,
                    "timestamp": exp.timestamp,
                    "tags": exp.tags,
                    "context": exp.context,
                },
                keywords=[exp.action] + list(exp.tags),
            )
        except Exception as e:
            logger.error(f"HAM write failed: {e}")

    async def _update_spatial(self, exp: GameExperience):
        """更新空間記憶（任務經驗＝真正在該地做事，計入親訪）。"""
        pos = exp.position
        loc_id = f"{int(pos[0])}_{int(pos[1])}_{int(pos[2])}"

        spot = self._spatial_index.get(loc_id)
        if spot is None:
            if len(self._spatial_index) >= self.MAX_SPATIAL:
                oldest = min(self._spatial_index.values(), key=lambda s: s.last_seen)
                del self._spatial_index[oldest.location_id]
            spot = SpatialMemory(
                location_id=loc_id,
                position=pos,
                node_type="unknown",
                resources={},
                last_seen=exp.timestamp,
            )
            self._spatial_index[loc_id] = spot
        spot.last_visited = max(spot.last_visited, exp.timestamp)
        spot.visit_count += 1

        node = self._spatial_index[loc_id]
        node.last_visited = exp.timestamp
        node.visit_count += 1

        # 根據經驗更新節點類型
        if "resource" in exp.tags:
            node.node_type = "resource"
            for res, count in exp.outcome.get("collected", {}).items():
                node.resources[res] = node.resources.get(res, 0) + count
        elif "danger" in exp.tags or exp.reward < -0.5:
            node.node_type = "danger"
            node.danger_level = max(node.danger_level, abs(exp.reward))
        elif "base" in exp.tags:
            node.node_type = "base"

    async def _update_procedural(self, exp: GameExperience):
        """更新程序記憶 (技能序列)"""
        chain_key = exp.context.get("goal", "unknown")
        action_seq = self._procedural_chains[chain_key]
        action_seq.append(exp.action)
        # 保留最近 20 步
        if len(action_seq) > 20:
            action_seq.pop(0)

    # ==================== 經驗檢索 ====================

    async def recall_experience(
        self,
        query: str,
        limit: int = 10,
        memory_type: Optional[MemoryType] = None,
        min_reward: float = -1.0,
    ) -> List[str]:
        """
        檢索相關經驗 (返回摘要字串列表)

        先查本地會話快取，再查 HAM 持久層，兩者合併去重。
        """
        results = []
        # 1. HAM 持久層 (真實調用)
        try:
            if self._ham is not None and hasattr(self._ham, "query_core_memory"):
                ham_hits = await self._ham.query_core_memory(
                    keywords=[query],
                    data_type_filter="game_experience",
                    limit=limit,
                )
                for hit in ham_hits or []:
                    content = getattr(hit, "content", hit)
                    if isinstance(content, dict):
                        summary = (
                            f"[ham] {content.get('action')} @ "
                            f"{content.get('position')} -> {content.get('outcome')}"
                        )
                    else:
                        summary = f"[ham] {content}"
                    results.append((1, summary))
        except Exception as e:
            logger.debug(f"HAM recall failed, using local only: {e}")
        query_lower = query.lower()

        for exp in reversed(self._experiences):  # 最新優先
            if memory_type and exp.memory_type != memory_type:
                continue
            if exp.reward < min_reward:
                continue

            # 簡單關鍵字匹配
            match_score = 0
            for tag in exp.tags:
                if tag.lower() in query_lower:
                    match_score += 2
            if query_lower in exp.action.lower():
                match_score += 3
            if query_lower in str(exp.context).lower():
                match_score += 1

            if match_score > 0:
                summary = f"[{exp.memory_type.value}] {exp.action} @ {exp.position} -> {exp.outcome} (reward: {exp.reward:.2f})"
                results.append((match_score, summary))

        results.sort(key=lambda x: -x[0])
        return [r[1] for r in results[:limit]]

    async def recall_successful_patterns(self, goal: str, limit: int = 5) -> List[List[str]]:
        """檢索成功的行為模式 (程序記憶)"""
        patterns = []
        for chain_key, actions in self._procedural_chains.items():
            if goal.lower() in chain_key.lower() and len(actions) > 2:
                patterns.append(actions)
        return patterns[:limit]

    # ==================== 配方查詢 ====================

    def get_recipe(self, recipe_id: str) -> Optional[RecipeMemory]:
        """查詢配方"""
        return self._recipes.get(recipe_id)

    def get_craftable_recipes(self, inventory: Dict[str, int]) -> List[RecipeMemory]:
        """根據背包獲取可製作配方（先折短名，否則 itemstring 永遠對不上）"""
        inventory = normalize_inventory(inventory)
        craftable = []
        for recipe in self._recipes.values():
            if not recipe.unlocked:
                continue
            can_craft = all(inventory.get(ing, 0) >= cnt for ing, cnt in recipe.ingredients.items())
            if can_craft:
                craftable.append(recipe)
        # 按熟練度/優先級排序
        craftable.sort(key=lambda r: -r.proficiency)
        return craftable

    def get_recipe_chain(self, target: str) -> List[RecipeMemory]:
        """獲取製作鏈 (遞歸依賴，包含 station)"""
        chain = []
        visited = set()

        def dfs(item):
            if item in visited:
                return
            visited.add(item)
            recipe = self._recipes.get(item)
            if recipe:
                # 先處理 ingredients
                for ing in recipe.ingredients:
                    dfs(ing)
                # 再處理 station
                if recipe.station and recipe.station != "crafting_table":
                    dfs(recipe.station)
                chain.append(recipe)

        dfs(target)
        return chain

    def get_all_recipe_dependencies(self, target: str) -> Set[str]:
        """獲取所有依賴的配方 ID (包含中間產物和 station)"""
        deps = set()
        visited = set()

        def dfs(item):
            if item in visited:
                return
            visited.add(item)
            recipe = self._recipes.get(item)
            if recipe:
                deps.add(recipe.recipe_id)
                for ing in recipe.ingredients:
                    dfs(ing)
                # 也遞歸處理 station
                if recipe.station and recipe.station != "crafting_table":
                    dfs(recipe.station)

        dfs(target)
        return deps

    # ==================== 空間查詢 ====================

    def find_nearest_resource(
        self, position: Tuple[float, float, float], resource: str, max_dist: float = 100
    ) -> Optional[SpatialMemory]:
        """尋找最近的資源點"""
        best = None
        best_dist = float("inf")

        for node in self._spatial_index.values():
            if hasattr(node, "resources") and isinstance(node.resources, dict):
                if resource in node.resources and node.resources[resource] > 0:
                    dist = self._distance(position, node.position)
                    if dist < best_dist and dist <= max_dist:
                        best_dist = dist
                        best = node
        return best

    def find_safe_location(
        self, position: Tuple[float, float, float], radius: float = 50
    ) -> Optional[SpatialMemory]:
        """尋找安全位置 (低危險、高訪問)"""
        best = None
        best_score = -1

        for node in self._spatial_index.values():
            dist = self._distance(position, node.position)
            if dist <= radius:
                score = node.visit_count * 0.1 - node.danger_level * 10
                if score > best_score:
                    best_score = score
                    best = node
        return best

    def mark_danger(self, position: Tuple[float, float, float], level: float = 1.0):
        """標記危險區"""
        loc_id = f"{int(position[0])}_{int(position[1])}_{int(position[2])}"
        if loc_id in self._spatial_index:
            self._spatial_index[loc_id].danger_level = max(
                self._spatial_index[loc_id].danger_level, level
            )
            self._spatial_index[loc_id].node_type = "danger"

    def mark_base(self, position: Tuple[float, float, float]):
        """標記基地位置"""
        loc_id = f"{int(position[0])}_{int(position[1])}_{int(position[2])}"
        if loc_id not in self._spatial_index:
            self._spatial_index[loc_id] = SpatialMemory(
                location_id=loc_id,
                position=position,
                node_type="base",
                resources={},
                last_visited=time.time(),
            )
        self._spatial_index[loc_id].node_type = "base"

    # ==================== 工具方法 ====================

    def _distance(self, a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
        return np.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    def get_stats(self) -> Dict[str, Any]:
        return {
            "experiences": len(self._experiences),
            "spatial_nodes": len(self._spatial_index),
            "recipes": len(self._recipes),
            "procedural_chains": len(self._procedural_chains),
        }


class MockHAMManager:
    """模擬 HAM Manager (測試用)"""

    def __init__(self):
        self.store_called = False

    async def store(self, *args, **kwargs):
        self.store_called = True

    async def recall(self, *args, **kwargs):
        return []
