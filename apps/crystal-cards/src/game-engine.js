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
        // Consume cards (remove dragged, reduce target)
        const consumeFromTarget = {};
        const consumeFromDragged = {};
        for (const [tid, needed] of Object.entries(map)) {
          const fromDrag = Math.min(needed, combined[tid] === targetId ? 0 : 0);
          // Simple: consume from dragged first, then target
          let remaining = needed;
          if (tid === dragId) {
            const take = Math.min(remaining, draggedCard.count);
            consumeFromDragged[tid] = take;
            remaining -= take;
          }
          if (tid === targetId) {
            const take = Math.min(remaining, targetCard.count);
            consumeFromTarget[tid] = take;
            remaining -= take;
          }
          if (remaining > 0 && tid !== dragId && tid !== targetId) {
            canCraft = false; break;
          }
          if (remaining > 0) canCraft = false;
        }

        if (!canCraft) continue;

        removeBoardCard(draggedCard.id);
        // Reduce target card count
        targetCard.count -= Object.values(consumeFromTarget).reduce((a, b) => a + b, 0);
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

  const atkDmg = Math.max(1, atkStats.atk - defStats.def / 2 + Math.floor(Math.random() * 5));
  const defDmg = Math.max(1, defStats.atk - atkStats.def / 2 + Math.floor(Math.random() * 3));

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
    const enemy = enemyPool[Math.floor(Math.random() * enemyPool.length)];
    const x = 100 + Math.random() * 600;
    const y = 100 + Math.random() * 400;
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
  ];

  // Only include items that are unlocked
  const filteredPool = pool.filter(p => {
    const template = getCardTemplate(p.id);
    if (template.type === 'location') return GameState.unlockedLocations.includes(p.id);
    return true;
  });

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
  // Reset state
  Object.assign(GameState, {
    hp: 100, maxHp: 100, sanity: 100, gold: 10, knowledge: 0,
    bonds: {}, day: 1, timeOfDay: 'morning', tickCount: 0,
    paused: false, speed: 1, boardCards: [], cardIdCounter: 0,
    sidebarCards: [], inventory: [],
    unlockedLocations: ['loc_holy_cross', 'loc_mirror_lake'],
    flags: {}, discoveredDialogues: [], log: [],
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
};
