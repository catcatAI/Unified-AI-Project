/**
 * game-engine.js — Core game loop and card management
 * Stacklands-style mechanics: time, cards, crafting, combat
 */

// Card data loaded via <script src="../game-data/cards.js">
// cards.js declares const CARDS, WORLD_LINES, NPC_SCHEDULES in global scope
// and sets window.CARDS_DATA = { CARDS, WORLD_LINES, NPC_SCHEDULES }
// We reference the global const directly (no redeclaration).
// These are already available as globals from cards.js.

// ═══════════════════════════════════════════════════════
// Game State
// ═══════════════════════════════════════════════════════
const GameState = {
  // Player stats
  hp: 100,
  maxHp: 100,
  sanity: 100,
  gold: 10,
  knowledge: 0,
  bonds: {}, // character_id -> value

  // Time
  day: 1,
  timeOfDay: 'morning', // morning, afternoon, evening, night
  tickCount: 0,
  ticksPerDay: 12, // 4 time periods × 3 ticks each
  paused: false,
  speed: 1, // 1x, 2x, 3x

  // Cards on the board
  boardCards: [],   // Array of { id, templateId, x, y, stackId, ... }
  cardIdCounter: 0,

  // Sidebar cards (available to place)
  sidebarCards: [],  // Array of { templateId, count }

  // Inventory (collected items)
  inventory: [], // Array of { templateId, count }

  // Unlocked locations & flags
  unlockedLocations: ['loc_holy_cross', 'loc_mirror_lake'],
  flags: {},
  discoveredDialogues: [],
  discoveredCards: [],

  // Crafting (merge basic + rpg recipes)
  recipes: [...(CARDS.recipes || []), ...(CARDS.rpgRecipes || []).map(r => {
    // Build a map of { templateId: quantity } for each ingredient
    const ingredientMap = {};
    for (const ing of (r.ingredients || [])) {
      const tid = 'rpg_item_' + ing.item;
      ingredientMap[tid] = (ingredientMap[tid] || 0) + (ing.quantity || 1);
    }
    return {
      inputs: (r.ingredients || []).map(i => 'rpg_item_' + i.item),
      ingredientMap,
      output: 'rpg_item_' + (r.resultItem || r.name), count: r.resultQty || 1,
      name: r.name,
    };
  })],

  // Event log
  log: [],

  // Settings
  volume: 0.7,
  language: 'zh-TW',
  quality: 'high',
  showTutorial: true,
};

// ═══════════════════════════════════════════════════════
// Card Template Lookup
// ═══════════════════════════════════════════════════════
function getCardTemplate(templateId) {
  if (!templateId) return null;
  for (const category of Object.values(CARDS)) {
    if (Array.isArray(category)) {
      const found = category.find(c => c.id === templateId);
      if (found) return found;
    }
  }
  return null;
}

function getCardType(templateId) {
  const t = getCardTemplate(templateId);
  return t ? t.type : null;
}

// Get the actual game board dimensions
function getBoardDimensions() {
  // Default dimensions, overridden by renderer
  return { width: 900, height: 600 };
}

// ═══════════════════════════════════════════════════════
// Board Card Management
// ═══════════════════════════════════════════════════════
function createBoardCard(templateId, x, y, extra = {}) {
  const template = getCardTemplate(templateId);
  if (!template) return null;

  const card = {
    id: ++GameState.cardIdCounter,
    templateId,
    x,
    y,
    stackId: null,
    hp: template.stats ? template.stats.hp : null,
    maxHp: template.stats ? template.stats.hp : null,
    count: 1,
    ...extra,
  };

  GameState.boardCards.push(card);
  return card;
}

function removeBoardCard(cardId) {
  const idx = GameState.boardCards.findIndex(c => c.id === cardId);
  if (idx !== -1) {
    GameState.boardCards.splice(idx, 1);
  }
}

function findCardsAt(x, y, radius = 60) {
  return GameState.boardCards.filter(c => {
    const dx = c.x - x;
    const dy = c.y - y;
    return Math.sqrt(dx * dx + dy * dy) < radius && c.id !== undefined;
  });
}

function findStackAt(x, y, excludeId = null) {
  // Find a stack target card near (x, y)
  const candidates = GameState.boardCards.filter(c => {
    if (c.id === excludeId) return false;
    const dx = c.x - x;
    const dy = c.y - y;
    return Math.sqrt(dx * dx + dy * dy) < 70;
  });
  return candidates[0] || null;
}

// ═══════════════════════════════════════════════════════
// Sidebar Card Management
// ═══════════════════════════════════════════════════════
function addToSidebar(templateId, count = 1) {
  const existing = GameState.sidebarCards.find(c => c.templateId === templateId);
  if (existing) {
    existing.count += count;
  } else {
    GameState.sidebarCards.push({ templateId, count });
  }
}

function removeFromSidebar(templateId, count = 1) {
  const existing = GameState.sidebarCards.find(c => c.templateId === templateId);
  if (existing) {
    existing.count = Math.max(0, existing.count - count);
    if (existing.count === 0) {
      GameState.sidebarCards = GameState.sidebarCards.filter(c => c.templateId !== templateId);
    }
    return true;
  }
  return false;
}

// ═══════════════════════════════════════════════════════
// Inventory Management
// ═══════════════════════════════════════════════════════
function addToInventory(templateId, count = 1) {
  const template = getCardTemplate(templateId);
  const maxStack = template && template.stackable ? (template.maxStack || 99) : 1;

  const existing = GameState.inventory.find(c => c.templateId === templateId);
  if (existing) {
    existing.count = Math.min(maxStack, existing.count + count);
  } else {
    GameState.inventory.push({ templateId, count: Math.min(maxStack, count) });
  }
}

function hasItem(templateId) {
  return GameState.inventory.some(c => c.templateId === templateId && c.count > 0);
}

function removeFromInventory(templateId, count = 1) {
  const existing = GameState.inventory.find(c => c.templateId === templateId);
  if (existing && existing.count >= count) {
    existing.count -= count;
    if (existing.count <= 0) {
      GameState.inventory = GameState.inventory.filter(c => c.templateId !== templateId);
    }
    return true;
  }
  return false;
}

// ═══════════════════════════════════════════════════════
// Stacking / Crafting Logic
// ═══════════════════════════════════════════════════════
function tryStack(draggedCard, targetCard) {
  const dragTemplate = getCardTemplate(draggedCard.templateId);
  const targetTemplate = getCardTemplate(targetCard.templateId);
  if (!dragTemplate || !targetTemplate) return null;

  // Same resource card → stack
  if (dragTemplate.type === 'resource' && targetTemplate.type === 'resource' &&
      draggedCard.templateId === targetCard.templateId) {
    const maxStack = dragTemplate.maxStack || 99;
    const total = draggedCard.count + targetCard.count;
    targetCard.count = Math.min(maxStack, total);
    removeBoardCard(draggedCard.id);
    return { type: 'stack', message: `${dragTemplate.name} ×${targetCard.count}` };
  }

  // Recipe matching — check if these two cards satisfy any recipe
  const dragId = draggedCard.templateId;
  const targetId = targetCard.templateId;

  for (const recipe of GameState.recipes) {
    // If recipe has ingredientMap (from rpgRecipes), use quantity-aware matching
    if (recipe.ingredientMap) {
      const map = { ...recipe.ingredientMap };
      // Count how many of each card we're combining
      const combined = {};
      combined[dragId] = (combined[dragId] || 0) + draggedCard.count;
      combined[targetId] = (combined[targetId] || 0) + targetCard.count;

      // Check if combined cards satisfy all ingredients
      let canCraft = true;
      for (const [tid, needed] of Object.entries(map)) {
        if ((combined[tid] || 0) < needed) { canCraft = false; break; }
      }

      if (canCraft) {
        // Calculate how much to consume from each card
        let draggedNeeded = 0;
        let targetNeeded = 0;
        for (const [tid, needed] of Object.entries(map)) {
          if (tid === dragId) draggedNeeded += needed;
          else if (tid === targetId) targetNeeded += needed;
          else { canCraft = false; break; }
        }
        if (!canCraft) continue;

        // Consume from dragged card (partial or full)
        draggedCard.count -= draggedNeeded;
        if (draggedCard.count <= 0) {
          removeBoardCard(draggedCard.id);
        }
        // Consume from target card
        targetCard.count -= targetNeeded;
        if (targetCard.count <= 0) removeBoardCard(targetCard.id);

        if (recipe.output.startsWith('item_') || recipe.output.startsWith('res_')) {
          addToInventory(recipe.output, recipe.count);
          return { type: 'craft', message: `✅ ${recipe.name}！獲得 ${getCardTemplate(recipe.output)?.name || recipe.output}` };
        } else {
          const newCard = createBoardCard(recipe.output, targetCard.x, targetCard.y);
          return { type: 'craft', message: `✅ ${recipe.name}！`, card: newCard };
        }
      }
    } else {
      // Legacy 2-input exact match (base recipes)
      const inputs = [...recipe.inputs].sort();
      const candidates = [draggedCard.templateId, targetCard.templateId].sort();

      if (inputs.length === 2 && inputs[0] === candidates[0] && inputs[1] === candidates[1]) {
        removeBoardCard(draggedCard.id);
        removeBoardCard(targetCard.id);

        if (recipe.output.startsWith('item_') || recipe.output.startsWith('res_')) {
          addToInventory(recipe.output, recipe.count);
          return { type: 'craft', message: `✅ ${recipe.name}！獲得 ${getCardTemplate(recipe.output)?.name || recipe.output}` };
        } else {
          const newCard = createBoardCard(recipe.output, targetCard.x, targetCard.y);
          return { type: 'craft', message: `✅ ${recipe.name}！`, card: newCard };
        }
      }
    }
  }

  // Character + Location → trigger dialogue
  if (dragTemplate.type === 'character' && targetTemplate.type === 'location') {
    if (targetCard.templateId === dragTemplate.location) {
      return { type: 'dialogue', dialogueId: dragTemplate.dialogue, character: dragTemplate };
    }
  }
  if (dragTemplate.type === 'location' && targetTemplate.type === 'character') {
    if (draggedCard.templateId === targetTemplate.location) {
      return { type: 'dialogue', dialogueId: targetTemplate.dialogue, character: targetTemplate };
    }
  }

  // Character + Enemy → combat
  if (dragTemplate.type === 'character' && targetTemplate.type === 'enemy') {
    return { type: 'combat', attacker: dragTemplate, defender: targetTemplate, attackerCard: draggedCard, defenderCard: targetCard };
  }

  // Item + Character → use item on character
  if (dragTemplate.type === 'item' && targetTemplate.type === 'character') {
    if (dragTemplate.category === 'consumable' || dragTemplate.category === 'food') {
      removeBoardCard(draggedCard.id);
      const heal = dragTemplate.category === 'food' ? 20 : 30;
      if (targetCard.hp !== null) {
        targetCard.hp = Math.min(targetCard.maxHp || 100, targetCard.hp + heal);
      }
      return { type: 'use', message: `${targetTemplate.name} 使用了 ${dragTemplate.name}，恢復 ${heal} HP` };
    }
  }

  // Location + Enemy → encounter
  if (dragTemplate.type === 'location' && targetTemplate.type === 'enemy') {
    return { type: 'combat', attacker: null, defender: targetTemplate, defenderCard: targetCard, locationCard: draggedCard };
  }

  return null;
}

// ═══════════════════════════════════════════════════════
// Combat System
// ═══════════════════════════════════════════════════════
function executeCombat(attackerTemplate, defenderTemplate, attackerCard, defenderCard) {
  const atkStats = attackerTemplate ? attackerTemplate.stats : { hp: 50, atk: 8, def: 5, spd: 10 };
  const defStats = defenderTemplate.stats;
  // Apply equipment bonus
  const eqBonus = getEquipmentBonus();
  const finalAtk = { ...atkStats, atk: (atkStats.atk || 0) + eqBonus.atk, def: (atkStats.def || 0) + eqBonus.def, spd: (atkStats.spd || 0) + eqBonus.spd };

  const atkDmg = Math.max(1, finalAtk.atk - (defStats.def || 0) / 2 + Math.floor(Math.random() * 5));
  const defDmg = Math.max(1, (defStats.atk || 0) - finalAtk.def / 2 + Math.floor(Math.random() * 3));

  const results = [];
  results.push({ text: `${attackerTemplate?.name || '你'} 攻擊 ${defenderTemplate.name}，造成 ${atkDmg} 傷害！`, type: 'damage' });

  if (defenderCard.hp !== null) {
    defenderCard.hp -= atkDmg;
    if (defenderCard.hp <= 0) {
      results.push({ text: `${defenderTemplate.name} 被擊敗！`, type: 'heal' });
      // Drop loot
      if (defenderTemplate.loot) {
        for (const lootId of defenderTemplate.loot) {
          const lootTemplate = getCardTemplate(lootId);
          if (lootTemplate && lootTemplate.type === 'resource') {
            addToInventory(lootId);
            results.push({ text: `獲得 ${lootTemplate.name}`, type: 'heal' });
          } else {
            addToSidebar(lootId);
            results.push({ text: `獲得 ${lootTemplate?.name || lootId}`, type: 'heal' });
          }
        }
      }
      removeBoardCard(defenderCard.id);
      return { results, won: true };
    }
  }

  results.push({ text: `${defenderTemplate.name} 反擊，造成 ${defDmg} 傷害！`, type: 'damage' });
  GameState.hp = Math.max(0, GameState.hp - defDmg);

  if (GameState.hp <= 0) {
    results.push({ text: '你倒下了...', type: 'damage' });
    return { results, won: false, gameOver: true };
  }

  return { results, won: false };
}

// ═══════════════════════════════════════════════════════
// Time System
// ═══════════════════════════════════════════════════════
function advanceTime() {
  if (GameState.paused) return;

  GameState.tickCount++;

  // Advance time of day
  const period = Math.floor(GameState.tickCount % GameState.ticksPerDay / 3);
  const periods = ['morning', 'afternoon', 'evening', 'night'];
  GameState.timeOfDay = periods[period];

  // New day
  if (GameState.tickCount > 0 && GameState.tickCount % GameState.ticksPerDay === 0) {
    GameState.day++;
  }

  // Generate resources and gold from location cards
  for (const card of GameState.boardCards) {
    const template = getCardTemplate(card.templateId);
    if (template && template.type === 'location' && template.resourceRate > 0) {
      if (GameState.tickCount % 3 === 0) {
        // Generate resources
        const resourcePool = CARDS.resources.filter(r => r.category === 'material' || r.category === 'herb' || r.category === 'food');
        if (resourcePool.length > 0 && Math.random() < template.resourceRate * 0.3) {
          const res = resourcePool[Math.floor(Math.random() * resourcePool.length)];
          addToSidebar(res.id);
        }
        // Generate gold (market locations generate more)
        const goldChance = template.resourceRate >= 2 ? 0.4 : 0.2;
        if (Math.random() < goldChance) {
          const goldAmount = template.resourceRate >= 2 ? 2 : 1;
          GameState.gold += goldAmount;
        }
        // Generate crystal shards (magic locations)
        if (template.worldLine === '迴廊' || template.worldLine === '夢境層') {
          if (Math.random() < 0.15) {
            addToSidebar('res_crystal_shard');
          }
        }
      }
    }

    // Characters at locations generate knowledge and gold

    // Apply location hpMod and sanMod (once per tick, per location)
    if (template.type === 'location') {
      if (template.hpMod) GameState.hp = Math.max(0, Math.min(GameState.maxHp, GameState.hp + template.hpMod * 0.1));
      if (template.sanMod) GameState.sanity = Math.max(0, Math.min(100, GameState.sanity + template.sanMod * 0.1));
    }
    if (template && template.type === 'character') {
      if (GameState.tickCount % 5 === 0) {
        GameState.knowledge = Math.min(100, GameState.knowledge + 1);
        // Characters also generate a small amount of gold
        if (Math.random() < 0.1) {
          GameState.gold += 1;
        }
      }
    }
  }

  // Night: sanity drain (reduced from -1 to -0.3 per tick)
  if (GameState.timeOfDay === 'night') {
    GameState.sanity = Math.max(0, GameState.sanity - 0.3);
  }

  // Enemy spawns (rare)
  if (GameState.day > 1 && Math.random() < 0.02) {
    const enemyPool = [...(CARDS.enemies || []), ...(CARDS.rpgEnemies || [])];
    if (enemyPool.length === 0) return;
    const enemy = enemyPool[Math.floor(Math.random() * enemyPool.length)];
    const x = 100 + Math.random() * 500;
    const y = 80 + Math.random() * 350;
    createBoardCard(enemy.id, x, y);
  }
}

// ═══════════════════════════════════════════════════════
// Drawing Cards from Sidebar
// ═══════════════════════════════════════════════════════
function drawCard() {
  const cost = 3 + Math.floor(GameState.day / 3);
  if (GameState.gold < cost) {
    return { success: false, message: `金幣不足！需要 ${cost} 💰` };
  }

  GameState.gold -= cost;

  // Random card from available pool
  const pool = [
    ...CARDS.resources.map(r => ({ id: r.id, weight: 5 })),
    ...CARDS.items.map(i => ({ id: i.id, weight: 2 })),
    ...(CARDS.rpgItems || []).map(i => ({ id: i.id, weight: 2 })),
    ...(CARDS.rpgHerbalItems || []).map(i => ({ id: i.id, weight: 3 })),
    ...(CARDS.rpgAnimalItems || []).map(i => ({ id: i.id, weight: 1 })),
    ...(CARDS.rpgNpcShopItems || []).map(i => ({ id: i.id, weight: 1 })),
    ...CARDS.characters.map(c => ({ id: c.id, weight: 3 })),
    ...CARDS.enemies.map(e => ({ id: e.id, weight: 1 })),
    ...(CARDS.rpgEnemies || []).map(e => ({ id: e.id, weight: 1 })),
    ...(CARDS.rpgNavalItems || []).map(i => ({ id: i.id, weight: 1 })),
    ...(CARDS.rpgNavalItemsMore || []).map(i => ({ id: i.id, weight: 1 })),
    ...(CARDS.rpgElementalItems || []).map(i => ({ id: i.id, weight: 1 })),
    ...(CARDS.storyEvents || []).map(e => ({ id: e.id, weight: 1 })),
  ];

  // Only include items that are unlocked and have valid templates
  const filteredPool = pool.filter(p => {
    const template = getCardTemplate(p.id);
    if (!template) return false;
    if (template.type === 'location') return GameState.unlockedLocations.includes(p.id);
    return true;
  });
  if (filteredPool.length === 0) {
    return { success: false, message: '沒有可抽取的卡片！' };
  }

  const totalWeight = filteredPool.reduce((sum, p) => sum + p.weight, 0);
  let roll = Math.random() * totalWeight;
  for (const item of filteredPool) {
    roll -= item.weight;
    if (roll <= 0) {
      return { success: true, templateId: item.id };
    }
  }

  return { success: true, templateId: filteredPool[0].id };
}

// ═══════════════════════════════════════════════════════
// Initialize New Game
// ═══════════════════════════════════════════════════════
function initNewGame() {
  // Reset state completely
  Object.assign(GameState, {
    hp: 100, maxHp: 100, sanity: 100, gold: 10, knowledge: 0,
    bonds: {}, day: 1, timeOfDay: 'morning', tickCount: 0,
    paused: false, speed: 1, boardCards: [], cardIdCounter: 0,
    sidebarCards: [], inventory: [],
    unlockedLocations: ['loc_holy_cross', 'loc_mirror_lake'],
    flags: {}, discoveredDialogues: [], discoveredCards: [], log: [],
    equipment: { weapon: null, armor: null, accessory: null },
  });

  // Starting cards in sidebar
  addToSidebar('loc_holy_cross', 1);
  addToSidebar('loc_mirror_lake', 1);
  addToSidebar('loc_market', 1);
  addToSidebar('res_food', 3);
  addToSidebar('res_wood', 2);
  addToSidebar('res_stone', 1);
  addToSidebar('res_water', 2);

  // Starting characters near their locations
  createBoardCard('char_hikuraya', 200, 300);
  createBoardCard('char_red', 500, 200);

  // Initial resources
  addToSidebar('item_flashlight', 1);
  addToSidebar('item_map', 1);

  return GameState;
}

// ═══════════════════════════════════════════════════════
// World Map — Location Navigation
// ═══════════════════════════════════════════════════════
const WORLD_MAP = {
  'loc_holy_cross': ['loc_mirror_lake', 'loc_yuyu_mountain', 'loc_clear_stream', 'loc_convenience_store', 'loc_agriculture', 'loc_library', 'loc_secret_ironworks'],
  'loc_mirror_lake': ['loc_holy_cross', 'loc_mirror_mountain'],
  'loc_yuyu_mountain': ['loc_holy_cross', 'loc_hot_spring', 'loc_market'],
  'loc_market': ['loc_yuyu_mountain', 'loc_fog_islands', 'loc_west_market'],
  'loc_fog_islands': ['loc_market'],
  'loc_convenience_store': ['loc_holy_cross', 'loc_forest'],
  'loc_forest': ['loc_convenience_store'],
  'loc_hot_spring': ['loc_yuyu_mountain'],
  'loc_clear_stream': ['loc_holy_cross', 'loc_abandoned_mine'],
  'loc_mirror_mountain': ['loc_mirror_lake', 'loc_hall_of_heroes'],
  'loc_abandoned_mine': ['loc_clear_stream', 'loc_rust_city'],
  'loc_hall_of_heroes': ['loc_mirror_mountain'],
  'loc_rust_city': ['loc_abandoned_mine'],
  'loc_library': ['loc_holy_cross', 'loc_corridor'],
  'loc_corridor': ['loc_library', 'loc_witch_academy'],
  'loc_witch_academy': ['loc_yuyu_mountain', 'loc_corridor'],
  'loc_orbital_station': ['loc_frozen_wastes'],
  'loc_frozen_wastes': ['loc_orbital_station', 'loc_fog_islands'],
  'loc_secret_ironworks': ['loc_holy_cross'],
  'loc_agriculture': ['loc_holy_cross', 'loc_witch_academy'],
  'loc_west_market': ['loc_market'],
};

function getAdjacentLocations(locationId) {
  return WORLD_MAP[locationId] || [];
}

function unlockAdjacentLocations(locationId) {
  const adjacent = getAdjacentLocations(locationId);
  const newUnlocks = [];
  adjacent.forEach(locId => {
    if (!GameState.unlockedLocations.includes(locId)) {
      GameState.unlockedLocations.push(locId);
      const template = getCardTemplate(locId);
      if (template) newUnlocks.push(template.name);
    }
  });
  return newUnlocks;
}

// Location → reward card type mapping for exploration
const LOCATION_REWARDS = {
  loc_library: { type: 'rule', pool: (CARDS.ruleCards || []) },
  loc_corridor: { type: 'story', pool: (CARDS.storyEvents || []).filter(s => s.trigger) },
  loc_holy_cross: { type: 'scene', pool: (CARDS.sceneCards || []).filter(s => s.name.includes('聖十字') || s.name.includes('校園')) },
  loc_mirror_lake: { type: 'scene', pool: (CARDS.sceneCards || []).filter(s => s.name.includes('鏡')) },
  loc_market: { type: 'shopCatalog', pool: (CARDS.rpgShopCatalogs || []) },
  loc_west_market: { type: 'shopCatalog', pool: (CARDS.rpgShopCatalogs || []) },
  loc_convenience_store: { type: 'shopCatalog', pool: (CARDS.rpgShopCatalogs || []).filter(s => s.name.includes('便利') || s.name.includes('雜貨')) },
  loc_witch_academy: { type: 'rule', pool: (CARDS.ruleCards || []).filter(s => s.name.includes('魔') || s.name.includes('迴廊')) },
  loc_fog_islands: { type: 'nation', pool: (CARDS.nationalCards || []).filter(s => s.name.includes('莫比') || s.name.includes('阿比')) },
  loc_frozen_wastes: { type: 'nation', pool: (CARDS.nationalCards || []).filter(s => s.name.includes('聖諭') || s.name.includes('冰')) },
  loc_yuyu_mountain: { type: 'scene', pool: (CARDS.sceneCards || []).filter(s => s.name.includes('鬱鬱') || s.name.includes('山')) },
  loc_mirror_mountain: { type: 'scene', pool: (CARDS.sceneCards || []).filter(s => s.name.includes('鏡山') || s.name.includes('卡洛夫')) },
  loc_abandoned_mine: { type: 'organization', pool: (CARDS.organizationCards || []).filter(s => s.name.includes('鐵') || s.name.includes('鼠') || s.name.includes('深海')) },
  loc_secret_ironworks: { type: 'organization', pool: (CARDS.organizationCards || []).filter(s => s.name.includes('工業') || s.name.includes('義體') || s.name.includes('防務')) },
  loc_hot_spring: { type: 'scene', pool: (CARDS.sceneCards || []).filter(s => s.name.includes('溫泉') || s.name.includes('煙雲')) },
  loc_clear_stream: { type: 'scene', pool: (CARDS.sceneCards || []).filter(s => s.name.includes('清溪')) },
  loc_agriculture: { type: 'organization', pool: (CARDS.organizationCards || []).filter(s => s.name.includes('農') || s.name.includes('海葵')) },
  loc_hall_of_heroes: { type: 'nation', pool: (CARDS.nationalCards || []) },
  loc_rust_city: { type: 'scene', pool: (CARDS.sceneCards || []).filter(s => s.name.includes('鏽蝕') || s.name.includes('W04')) },
  loc_orbital_station: { type: 'scene', pool: (CARDS.sceneCards || []).filter(s => s.name.includes('軌道') || s.name.includes('大學院')) },
  loc_forest: { type: 'organization', pool: (CARDS.organizationCards || []).filter(s => s.name.includes('貓') || s.name.includes('海盜') || s.name.includes('藍鰭')) },
};

// Try to find a reward card from exploring a location
function exploreLocationRewards(locationId) {
  const reward = LOCATION_REWARDS[locationId];
  if (!reward || !reward.pool || reward.pool.length === 0) return null;

  // 40% chance to find something
  if (Math.random() > 0.4) return null;

  // Find cards not yet discovered
  const undiscovered = reward.pool.filter(c => !GameState.discoveredCards.includes(c.id));
  const pool = undiscovered.length > 0 ? undiscovered : reward.pool;

  const found = pool[Math.floor(Math.random() * pool.length)];
  if (!found) return null;

  if (!GameState.discoveredCards.includes(found.id)) {
    GameState.discoveredCards.push(found.id);
  }
  addToSidebar(found.id);
  return { name: found.name, type: reward.type, icon: found.icon || '📋' };
}

// ═══════════════════════════════════════════════════════
// Shop System — Buy/Sell with Gold
// ═══════════════════════════════════════════════════════
function buyItem(templateId, cost) {
  if (GameState.gold < cost) return { success: false, message: '金幣不足！' };
  const template = getCardTemplate(templateId);
  if (!template) return { success: false, message: '物品不存在！' };
  GameState.gold -= cost;
  if (template.type === 'resource' || template.type === 'item') {
    addToSidebar(templateId);
  } else {
    createBoardCard(templateId, 300 + Math.random() * 400, 200 + Math.random() * 300);
  }
  return { success: true, message: `購買了 ${template.name}！` };
}

function sellItem(templateId, price) {
  if (removeFromSidebar(templateId) || removeFromInventory(templateId)) {
    GameState.gold += price;
    return { success: true, message: `賣出了 ${getCardTemplate(templateId)?.name || templateId}！` };
  }
  return { success: false, message: '沒有可賣的物品！' };
}

function getShopPrices(templateId) {
  const template = getCardTemplate(templateId);
  if (!template) return null;
  const baseValue = template.value || 10;
  return { buy: Math.ceil(baseValue * 1.5), sell: Math.floor(baseValue * 0.5) };
}

// ═══════════════════════════════════════════════════════
// Equipment System
// ═══════════════════════════════════════════════════════
GameState.equipment = { weapon: null, armor: null, accessory: null };

function equipItem(cardId, slot) {
  if (!['weapon', 'armor', 'accessory'].includes(slot)) return { success: false, message: '無效的裝備欄位' };
  const card = GameState.boardCards.find(c => c.id === cardId);
  if (!card) return { success: false, message: '卡片不存在' };
  const template = getCardTemplate(card.templateId);
  if (!template) return { success: false, message: '模板不存在' };
  if (template.type !== 'item' && template.type !== 'resource') {
    return { success: false, message: '只能裝備物品或資源' };
  }
  // Unequip current item in slot
  if (GameState.equipment[slot]) {
    addToSidebar(GameState.equipment[slot]);
  }
  GameState.equipment[slot] = card.templateId;
  removeBoardCard(cardId);
  return { success: true, message: `裝備了 ${template.name}！` };
}

function unequipItem(slot) {
  if (GameState.equipment[slot]) {
    addToSidebar(GameState.equipment[slot]);
    const name = getCardTemplate(GameState.equipment[slot])?.name || '';
    GameState.equipment[slot] = null;
    return { success: true, message: `卸下了 ${name}！` };
  }
  return { success: false };
}

function getEquipmentBonus() {
  const bonus = { atk: 0, def: 0, spd: 0 };
  Object.values(GameState.equipment).forEach(templateId => {
    if (!templateId) return;
    const t = getCardTemplate(templateId);
    if (t && t.stats) {
      bonus.atk += t.stats.atk || 0;
      bonus.def += t.stats.def || 0;
      bonus.spd += t.stats.spd || 0;
    }
  });
  return bonus;
}

// ═══════════════════════════════════════════════════════
// Save / Load
// ═══════════════════════════════════════════════════════
function saveGame() {
  try {
    const data = JSON.stringify({
      hp: GameState.hp, maxHp: GameState.maxHp, sanity: GameState.sanity,
      gold: GameState.gold, knowledge: GameState.knowledge,
      bonds: GameState.bonds, day: GameState.day, timeOfDay: GameState.timeOfDay,
      tickCount: GameState.tickCount, sidebarCards: GameState.sidebarCards,
      inventory: GameState.inventory, unlockedLocations: GameState.unlockedLocations,
      flags: GameState.flags, discoveredDialogues: GameState.discoveredDialogues, discoveredCards: GameState.discoveredCards,
      equipment: GameState.equipment, volume: GameState.volume,
      boardCards: GameState.boardCards.map(c => ({
        templateId: c.templateId, x: c.x, y: c.y, hp: c.hp, maxHp: c.maxHp,
      })),
    });
    localStorage.setItem('crystal-cards-save', data);
    return true;
  } catch (e) {
    console.error('Save failed:', e);
    return false;
  }
}

function loadGame() {
  try {
    const raw = localStorage.getItem('crystal-cards-save');
    if (!raw) return false;
    const data = JSON.parse(raw);
    // Validate required fields
    if (typeof data.hp !== 'number' || !Array.isArray(data.boardCards)) {
      localStorage.removeItem('crystal-cards-save');
      return false;
    }
    // Restore all state fields
    GameState.hp = data.hp ?? 100;
    GameState.maxHp = data.maxHp ?? 100;
    GameState.sanity = data.sanity ?? 100;
    GameState.gold = data.gold ?? 10;
    GameState.knowledge = data.knowledge ?? 0;
    GameState.bonds = data.bonds ?? {};
    GameState.day = data.day ?? 1;
    GameState.timeOfDay = data.timeOfDay ?? 'morning';
    GameState.tickCount = data.tickCount ?? 0;
    GameState.sidebarCards = data.sidebarCards ?? [];
    GameState.inventory = data.inventory ?? [];
    GameState.unlockedLocations = data.unlockedLocations ?? ['loc_holy_cross', 'loc_mirror_lake'];
    GameState.flags = data.flags ?? {};
    GameState.discoveredDialogues = data.discoveredDialogues ?? [];
    GameState.discoveredCards = data.discoveredCards ?? [];
    GameState.equipment = data.equipment ?? { weapon: null, armor: null, accessory: null };
    GameState.volume = data.volume ?? 0.7;
    // Recreate board cards from saved data
    GameState.boardCards = [];
    GameState.cardIdCounter = 0;
    (data.boardCards || []).forEach(saved => {
      if (!saved.templateId) return; // skip invalid entries
      const card = {
        id: ++GameState.cardIdCounter,
        templateId: saved.templateId,
        x: saved.x || 0, y: saved.y || 0,
        stackId: null,
        hp: saved.hp, maxHp: saved.maxHp, count: 1,
      };
      GameState.boardCards.push(card);
    });
    return true;
  } catch (e) {
    console.error('Load failed:', e);
    localStorage.removeItem('crystal-cards-save');
    return false;
  }
}

// Auto-save every action
function autoSave() {
  try { saveGame(); } catch (e) {}
}

// ═══════════════════════════════════════════════════════
// Public API
// ═══════════════════════════════════════════════════════
window.GameEngine = {
  state: GameState,
  initNewGame,
  createBoardCard,
  removeBoardCard,
  findCardsAt,
  findStackAt,
  tryStack,
  executeCombat,
  advanceTime,
  drawCard,
  addToSidebar,
  removeFromSidebar,
  addToInventory,
  removeFromInventory,
  hasItem,
  getCardTemplate,
  getCardType,
  getAdjacentLocations,
  unlockAdjacentLocations,
  exploreLocationRewards,
  buyItem,
  sellItem,
  getShopPrices,
  equipItem,
  unequipItem,
  getEquipmentBonus,
  saveGame,
  loadGame,
  autoSave,
};
