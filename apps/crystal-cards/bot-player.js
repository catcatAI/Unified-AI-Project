#!/usr/bin/env node
/**
 * bot-player.js — AI Bot Player for Crystal Cards
 * Simulates a full game session (30 days), making strategic decisions.
 * Calls Angela AI API for NPC dialogue decisions.
 * Outputs a detailed play report.
 */

// ═══════════════════════════════════════════════════════
// Mock Browser Globals for Node.js
// ═══════════════════════════════════════════════════════
global.window = {};
global.document = {
  readyState: 'complete',
  getElementById: () => ({
    addEventListener: () => {},
    classList: { add: () => {}, remove: () => {} },
    innerHTML: '', textContent: '', style: {},
    appendChild: () => {},
    querySelectorAll: () => [],
  }),
  querySelectorAll: () => [],
  addEventListener: () => {},
};
global.requestAnimationFrame = () => {};
global.setTimeout = global.setTimeout;
global.WebSocket = null;

// Load card data
const fs = require('fs');
const path = require('path');

const cardsRaw = fs.readFileSync(path.join(__dirname, 'game-data', 'cards.js'), 'utf-8');
const cardsClean = cardsRaw
  .replace(/if \(typeof module.*[\s\S]*$/, '')  // Remove module.exports block at end
  + 'window.CARDS_DATA = { CARDS, WORLD_LINES, NPC_SCHEDULES };';
eval(cardsClean);

// Load game engine
const engineRaw = fs.readFileSync(path.join(__dirname, 'src', 'game-engine.js'), 'utf-8');
eval(engineRaw);

const E = window.GameEngine;
const { CARDS, WORLD_LINES } = window.CARDS_DATA;

// ═══════════════════════════════════════════════════════
// Angela AI Client
// ═══════════════════════════════════════════════════════
const http = require('http');

async function callAngela(message, context = {}) {
  const body = JSON.stringify({
    message,
    context: { source: 'crystal-cards-bot', ...context },
  });

  return new Promise((resolve) => {
    const req = http.request('http://127.0.0.1:8000/chat/unified', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
      timeout: 5000,
    }, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          resolve(json.response || json.response_text || json.message || '');
        } catch { resolve(''); }
      });
    });
    req.on('error', () => resolve(''));
    req.on('timeout', () => { req.destroy(); resolve(''); });
    req.write(body);
    req.end();
  });
}

// ═══════════════════════════════════════════════════════
// Play Report Logger
// ═══════════════════════════════════════════════════════
const report = {
  startTime: new Date().toISOString(),
  angelaConnected: false,
  totalDays: 0,
  events: [],
  combatLog: [],
  dialogueLog: [],
  craftingLog: [],
  discoveries: [],
  bugs: [],
  balanceIssues: [],
  finalState: null,
  decisions: [],
};

function logEvent(day, time, type, detail) {
  report.events.push({ day, time, type, detail });
}

function logBug(severity, description, context) {
  report.bugs.push({ severity, description, context });
}

function logBalance(description) {
  report.balanceIssues.push(description);
}

// ═══════════════════════════════════════════════════════
// AI Decision Engine
// ═══════════════════════════════════════════════════════
function decideAction(state) {
  const decisions = [];
  const boardChars = state.boardCards.filter(c => E.getCardType(c.templateId) === 'character');
  const boardLocs = state.boardCards.filter(c => E.getCardType(c.templateId) === 'location');
  const boardEnemies = state.boardCards.filter(c => E.getCardType(c.templateId) === 'enemy');
  const boardResources = state.boardCards.filter(c => E.getCardType(c.templateId) === 'resource');
  const drawCost = 3 + Math.floor(state.day / 3);

  // ── Priority 10: Survival ──
  if (state.hp < 30) {
    const healItem = state.inventory.find(i => {
      const t = E.getCardTemplate(i.templateId);
      return t?.category === 'consumable' || t?.category === 'food';
    });
    if (healItem) decisions.push({ action: 'use_heal', priority: 10, reason: 'HP critically low' });
    decisions.push({ action: 'rest', priority: 10, reason: 'HP critically low' });
  }
  if (state.sanity < 20) {
    decisions.push({ action: 'rest', priority: 9, reason: 'Sanity critically low' });
  }

  // ── Priority 9: Place unlocked locations on board ──
  const exploredLocs = boardLocs.map(c => c.templateId);
  for (const locId of state.unlockedLocations) {
    if (!exploredLocs.includes(locId)) {
      if (totalPlaceDecisions < 15) decisions.push({ action: 'place_card', templateId: locId, priority: 9, reason: `Place new location ${E.getCardTemplate(locId)?.name}` });
    }
  }

  // ── Priority 8: Draw cards (if we have gold) ──
  if (state.gold >= drawCost) {
    decisions.push({ action: 'draw', priority: 8, reason: `Draw card (${drawCost} gold)` });
  }

  // ── Priority 7: Craft (check both board and sidebar) ──
  for (const recipe of CARDS.recipes) {
    const hasOnBoard = recipe.inputs.every(i => boardResources.some(r => r.templateId === i));
    const hasInSidebar = recipe.inputs.every(i => state.sidebarCards.some(s => s.templateId === i));
    if (hasOnBoard || hasInSidebar) {
      decisions.push({ action: 'craft', recipe, priority: 7, reason: `Craft ${recipe.name}` });
    }
  }

  // ── Priority 6: Place resources needed for recipes (max 20 total) ──
  if (!state._placeCount) state._placeCount = 0;
  if (state._placeCount < 20 && boardResources.length < 3 && state.boardCards.length < 12) {
    for (const recipe of CARDS.recipes) {
      const neededForRecipe = {};
      recipe.inputs.forEach(i => neededForRecipe[i] = (neededForRecipe[i] || 0) + 1);
      for (const [resId, needed] of Object.entries(neededForRecipe)) {
        const onBoard = boardResources.filter(r => r.templateId === resId).length;
        const inSidebar = state.sidebarCards.find(s => s.templateId === resId && s.count > 0);
        if (inSidebar && onBoard < needed) {
          if (totalPlaceDecisions < 15) decisions.push({ action: 'place_card', templateId: resId, priority: 6, reason: `Place ${E.getCardTemplate(resId)?.name} for crafting` });
          break;
        }
      }
      if (decisions.some(d => d.action === 'place_card')) break;
    }
  }

  // ── Priority 8: Talk to characters (skip if dialogue already completed) ──
  for (const char of boardChars) {
    const charTemplate = E.getCardTemplate(char.templateId);
    if (charTemplate?.dialogue && !completedDialogues.has(charTemplate.dialogue)) {
      const matchLoc = boardLocs.find(l => l.templateId === charTemplate.location);
      if (matchLoc) {
        decisions.push({
          action: 'stack', cardA: char.id, cardB: matchLoc.id,
          priority: 8, reason: `Talk to ${charTemplate.name}`
        });
      }
    }
  }

  // ── Priority 5: Fight enemies (if we have characters) ──
  if (boardChars.length > 0 && boardEnemies.length > 0) {
    const weakest = boardEnemies.reduce((w, e) => {
      const t = E.getCardTemplate(e.templateId);
      const wt = E.getCardTemplate(w.templateId);
      return (t?.stats?.hp || 999) < (wt?.stats?.hp || 999) ? e : w;
    }, boardEnemies[0]);
    decisions.push({
      action: 'stack', cardA: boardChars[0].id, cardB: weakest.id,
      priority: 5, reason: `Fight ${E.getCardTemplate(weakest.templateId)?.name}`
    });
  }

  // ── Priority 3: Place items on board (max 20 total) ──
  if (state._placeCount < 20 && state.boardCards.length < 12) {
    const itemsInSidebar = state.sidebarCards.filter(s => E.getCardType(s.templateId) === 'item');
    if (itemsInSidebar.length > 0) {
      if (totalPlaceDecisions < 15) decisions.push({ action: 'place_card', templateId: itemsInSidebar[0].templateId, priority: 3, reason: 'Place item on board' });
    }
  }

  // ── Priority 2: Rest (when nothing else to do) ──
  decisions.push({ action: 'rest', priority: 2, reason: 'Free rest' });

  // Sort by priority, pick best
  decisions.sort((a, b) => b.priority - a.priority);
  return decisions[0] || null;
}

// ═══════════════════════════════════════════════════════
// Execute Decision
// ═══════════════════════════════════════════════════════
async function executeDecision(decision, state) {
  if (!decision) return;

  report.decisions.push({ day: state.day, time: state.timeOfDay, decision });

  switch (decision.action) {
    case 'draw': {
      const result = E.drawCard();
      if (result.success) {
        E.addToSidebar(result.templateId);
        const t = E.getCardTemplate(result.templateId);
        logEvent(state.day, state.timeOfDay, 'draw', `Drew ${t?.name || result.templateId}`);
      } else {
        logEvent(state.day, state.timeOfDay, 'draw_failed', result.message);
      }
      break;
    }

    case 'place_card': {
      totalPlaceDecisions++;
      if (E.removeFromSidebar(decision.templateId)) {
        const x = 80 + Math.random() * 500;
        const y = 80 + Math.random() * 350;
        const card = E.createBoardCard(decision.templateId, x, y);
        if (card) {
          const t = E.getCardTemplate(decision.templateId);
          logEvent(state.day, state.timeOfDay, 'place', `Placed ${t?.name || decision.templateId}`);
        }
      }
      break;
    }

    case 'stack': {
      const cardA = state.boardCards.find(c => c.id === decision.cardA);
      const cardB = state.boardCards.find(c => c.id === decision.cardB);
      if (cardA && cardB) {
        const result = E.tryStack(cardA, cardB);
        if (result) {
          handleStackResult(result, state);
        }
      }
      break;
    }

    case 'use_heal': {
      const healItem = state.inventory.find(i => {
        const t = E.getCardTemplate(i.templateId);
        return t?.category === 'consumable' || t?.category === 'food';
      });
      if (healItem) {
        E.removeFromInventory(healItem.templateId);
        state.hp = Math.min(state.maxHp, state.hp + 30);
        const t = E.getCardTemplate(healItem.templateId);
        logEvent(state.day, state.timeOfDay, 'heal', `Used ${t?.name} (+30 HP)`);
      }
      break;
    }

    case 'rest': {
      state.sanity = Math.min(100, state.sanity + 15);
      state.hp = Math.min(state.maxHp, state.hp + 5);
      logEvent(state.day, state.timeOfDay, 'rest', `Rested (+15 SAN, +5 HP)`);
      break;
    }

    case 'craft': {
      const recipe = decision.recipe;
      let canCraft = true;
      // Try to consume from board first, then sidebar
      for (const input of recipe.inputs) {
        // Try removing from board resources
        const boardRes = state.boardCards.find(c => c.templateId === input && E.getCardType(c.templateId) === 'resource');
        if (boardRes) {
          E.removeBoardCard(boardRes.id);
          continue;
        }
        // Try sidebar
        if (E.removeFromSidebar(input)) {
          continue;
        }
        // Try inventory
        if (E.removeFromInventory(input)) {
          continue;
        }
        canCraft = false;
        break;
      }
      if (canCraft) {
        if (recipe.output.startsWith('item_') || recipe.output.startsWith('res_')) {
          E.addToInventory(recipe.output, recipe.count);
        } else {
          const card = E.createBoardCard(recipe.output, 300, 200);
        }
        const t = E.getCardTemplate(recipe.output);
        logEvent(state.day, state.timeOfDay, 'craft', `Crafted ${recipe.name} → ${t?.name || recipe.output}`);
        report.craftingLog.push({ day: state.day, recipe: recipe.name, output: t?.name });
      }
      break;
    }
  }
}

function handleStackResult(result, state) {
  switch (result.type) {
    case 'dialogue': {
      logEvent(state.day, state.timeOfDay, 'dialogue', `Dialogue: ${result.dialogueId}`);
      report.dialogueLog.push({
        day: state.day,
        character: result.character?.name,
        dialogueId: result.dialogueId,
      });
      // Auto-advance dialogue: select first available choice
      autoAdvanceDialogue(result.dialogueId, state);
      break;
    }
    case 'combat':
      logEvent(state.day, state.timeOfDay, 'combat', `Combat with ${result.defender?.name}`);
      const combatResult = E.executeCombat(result.attacker, result.defender, result.attackerCard, result.defenderCard);
      combatResult.results.forEach(r => {
        report.combatLog.push({ day: state.day, text: r.text, type: r.type });
      });
      break;
    case 'craft':
      logEvent(state.day, state.timeOfDay, 'craft', result.message);
      break;
    case 'stack':
      logEvent(state.day, state.timeOfDay, 'stack', result.message);
      break;
  }
}

// ═══════════════════════════════════════════════════════
// Angela-Powered NPC Dialogue
// ═══════════════════════════════════════════════════════
async function angelaNPCDialogue(characterName, context) {
  if (!report.angelaConnected) return null;

  const backstory = {
    '晞咕萊雅': '你是圖書館管理員晞咕萊雅，蛇尾種族，與迴廊有聯繫但失去了情感。語氣冷靜理性。',
    '紅': '你是市集商販紅，紅髮女孩，語氣直接而熱情。',
    '守門人': '你是鏡湖守門人，語氣深沉而神秘。',
    '翅翼少女': '你是書中的翅翼少女，有金屬翅膀，語氣溫柔而困惑。',
    '記憶老人': '你是記憶老人，語氣緩慢而智慧。',
  };

  const prompt = `你是「${characterName}」。${backstory[characterName] || ''}
玩家對你說：「${context.playerAction || '你好'}」
請用角色語氣回應（1-2句）。`;

  const response = await callAngela(prompt, { character: characterName });
  return response || null;
}

// ═══════════════════════════════════════════════════════
// Bug Detection
// ═══════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════
// Auto-advance Dialogue (select best choice)
// ═══════════════════════════════════════════════════════
let dialogueDepth = 0;
const completedDialogues = new Set();
let balanceIssueLogged = false;
let totalPlaceDecisions = 0; // Global counter for place_card decisions
function autoAdvanceDialogue(dialogueId, state) {
  if (dialogueDepth > 10) { dialogueDepth = 0; return; }
  dialogueDepth++;

  const dialogue = CARDS.dialogues[dialogueId];
  if (!dialogue || !dialogue.choices || dialogue.choices.length === 0) {
    dialogueDepth = 0;
    return;
  }

  // Skip if we've already completed this exact dialogue path
  if (completedDialogues.has(dialogueId)) {
    dialogueDepth = 0;
    return;
  }
  completedDialogues.add(dialogueId);

  // Find best choice: prefer choices that advance the story (have .next), skip ones we've done
  let bestChoice = null;
  let bestPriority = -1;

  for (const choice of dialogue.choices) {
    let available = true;
    if (choice.requires) {
      if (choice.requires.knowledge && state.knowledge < choice.requires.knowledge) available = false;
      if (choice.requires.item && !E.hasItem(choice.requires.item)) available = false;
    }
    if (!available) continue;

    // Priority: story-advancing choices first, then skill checks, then generic
    let priority = 0;
    if (choice.effect?.unlock) priority += 10; // Unlocking new areas
    if (choice.effect?.items) priority += 8; // Getting items
    if (choice.effect?.knowledge) priority += 5; // Gaining knowledge
    if (choice.skillCheck) priority += 3; // Skill checks (story gated)
    if (choice.effect?.bond) priority += 2; // Bond changes
    if (choice.next && !completedDialogues.has(choice.next)) priority += 1;
    if (choice.text.includes('離開') || choice.text === '離開') priority -= 5; // Avoid leaving

    if (priority > bestPriority) {
      bestPriority = priority;
      bestChoice = choice;
    }
  }

  if (bestChoice) {
    // Apply effects
    if (bestChoice.effect) {
      const e = bestChoice.effect;
      if (e.knowledge) state.knowledge = Math.min(100, state.knowledge + e.knowledge);
      if (e.gold) state.gold += e.gold;
      if (e.hp) state.hp = Math.min(state.maxHp, state.hp + e.hp);
      if (e.sanity) state.sanity = Math.min(100, state.sanity + e.sanity);
      if (e.unlock) {
        if (e.unlock.startsWith('loc_') && !state.unlockedLocations.includes(e.unlock)) {
          state.unlockedLocations.push(e.unlock);
          logEvent(state.day, state.timeOfDay, 'unlock', `Unlocked ${E.getCardTemplate(e.unlock)?.name || e.unlock}`);
        } else {
          state.flags[e.unlock] = true;
        }
      }
      if (e.unlocks) {
        for (const uid of e.unlocks) {
          if (uid.startsWith('loc_') && !state.unlockedLocations.includes(uid)) {
            state.unlockedLocations.push(uid);
            logEvent(state.day, state.timeOfDay, 'unlock', `Unlocked ${E.getCardTemplate(uid)?.name || uid}`);
          } else {
            state.flags[uid] = true;
          }
        }
      }
      if (e.items) {
        for (const itemId of e.items) {
          E.addToInventory(itemId);
          logEvent(state.day, state.timeOfDay, 'item', `Got ${E.getCardTemplate(itemId)?.name || itemId}`);
        }
      }
      if (e.bond) {
        for (const [npcId, delta] of Object.entries(e.bond)) {
          state.bonds[npcId] = Math.max(0, Math.min(100, (state.bonds[npcId] || 50) + delta));
        }
      }
    }
    // Continue to next dialogue
    if (bestChoice.next) {
      logEvent(state.day, state.timeOfDay, 'dialogue_choice', `${dialogue.speaker}: "${bestChoice.text}" → ${bestChoice.next}`);
      autoAdvanceDialogue(bestChoice.next, state);
    } else {
      logEvent(state.day, state.timeOfDay, 'dialogue_end', `${dialogue.speaker}: "${bestChoice.text}"`);
    }
  }
  dialogueDepth = 0;
}

function detectBugs(state) {
  // Check for negative values
  if (state.hp < 0) logBug('critical', 'HP went negative', { hp: state.hp });
  if (state.sanity < 0) logBug('critical', 'Sanity went negative', { sanity: state.sanity });
  if (state.gold < 0) logBug('high', 'Gold went negative', { gold: state.gold });

  // Check for orphaned cards
  for (const card of state.boardCards) {
    if (!E.getCardTemplate(card.templateId)) {
      logBug('high', `Orphaned card: ${card.templateId}`, { cardId: card.id });
    }
  }

  // Check for stuck states
  if (state.boardCards.length === 0 && state.sidebarCards.length === 0) {
    logBug('critical', 'No cards available — game is stuck', { day: state.day });
  }

  // Balance checks
  if (state.day > 5 && state.knowledge < 5) {
    logBalance('Knowledge too low after 5 days — might be stuck');
  }
  if (!balanceIssueLogged && state.day === 15 && !state.flags['unlocked_corridor'] && !state.unlockedLocations.includes('loc_corridor')) {
    logBalance('Corridor not unlocked by day 15 — story progression too slow');
    balanceIssueLogged = true;
  }
  if (state.gold > 100) {
    logBalance('Gold too high — economy might be unbalanced');
  }
}

// ═══════════════════════════════════════════════════════
// Main Game Loop
// ═══════════════════════════════════════════════════════
async function runGame() {
  console.log('🎮 Crystal Cards — AI Bot Player Starting...\n');

  // Check Angela connection
  try {
    const testResp = await callAngela('ping');
    report.angelaConnected = !!testResp;
    console.log(`🤖 Angela AI: ${report.angelaConnected ? '✅ Connected' : '❌ Offline (using fallbacks)'}`);
  } catch {
    report.angelaConnected = false;
    console.log('🤖 Angela AI: ❌ Offline (using fallbacks)');
  }

  // Initialize game
  E.initNewGame();
  const state = E.state;

  console.log(`\n═══ Game Start ═══`);
  console.log(`Day: ${state.day} | HP: ${state.hp} | SAN: ${state.sanity} | Gold: ${state.gold}`);
  console.log(`Board cards: ${state.boardCards.length} | Sidebar: ${state.sidebarCards.length}`);
  console.log(`Locations unlocked: ${state.unlockedLocations.join(', ')}\n`);

  // Place starting locations on board
  for (const locId of state.unlockedLocations) {
    if (E.removeFromSidebar(locId)) {
      const x = 80 + Math.random() * 400;
      const y = 80 + Math.random() * 300;
      E.createBoardCard(locId, x, y);
      logEvent(state.day, 'morning', 'place', `Placed ${E.getCardTemplate(locId)?.name}`);
    }
  }

  // Simulate 30 days
  const MAX_DAYS = 30;
  const TICKS_PER_DAY = 12;

  for (let day = 1; day <= MAX_DAYS; day++) {
    state.day = day;

    for (let tick = 0; tick < TICKS_PER_DAY; tick++) {
      const periods = ['morning', 'afternoon', 'evening', 'night'];
      state.timeOfDay = periods[Math.floor(tick / 3)];
      state.tickCount++;

      // Make 1-3 decisions per tick
      const numDecisions = 1 + Math.floor(Math.random() * 2);
      for (let d = 0; d < numDecisions; d++) {
        const decision = decideAction(state);
        if (decision) {
          await executeDecision(decision, state);
        }
      }

      // Time advance
      E.advanceTime();

      // Angela dialogue attempt (once per day, afternoon)
      if (state.timeOfDay === 'afternoon' && tick % 3 === 0 && report.angelaConnected) {
        const chars = state.boardCards.filter(c => E.getCardType(c.templateId) === 'character');
        if (chars.length > 0) {
          const char = chars[Math.floor(Math.random() * chars.length)];
          const template = E.getCardTemplate(char.templateId);
          if (template) {
            const dialogue = await angelaNPCDialogue(template.name, {
              playerAction: '你好',
              day: state.day,
            });
            if (dialogue) {
              logEvent(state.day, state.timeOfDay, 'angela_dialogue',
                `${template.name}: "${dialogue.slice(0, 50)}..."`);
              report.dialogueLog.push({
                day: state.day, character: template.name, source: 'angela', text: dialogue,
              });
            }
          }
        }
      }

      // Night sanity drain
      if (state.timeOfDay === 'night') {
        state.sanity = Math.max(0, state.sanity - 1);
      }

      // Detect bugs
      detectBugs(state);

      // Game over check
      if (state.hp <= 0) {
        logEvent(state.day, state.timeOfDay, 'game_over', 'Player died');
        console.log(`💀 Game Over on Day ${state.day}`);
        report.totalDays = day;
        report.finalState = { ...state };
        printReport();
        return;
      }
    }

    // Day summary
    const boardTypes = {};
    state.boardCards.forEach(c => {
      const t = E.getCardType(c.templateId);
      boardTypes[t] = (boardTypes[t] || 0) + 1;
    });

    if (day % 5 === 0 || day === 1) {
      console.log(`📅 Day ${day}: HP=${state.hp} SAN=${state.sanity} Gold=${state.gold} Knowledge=${state.knowledge}`);
      console.log(`   Board: ${JSON.stringify(boardTypes)} | Sidebar: ${state.sidebarCards.length} | Inventory: ${state.inventory.length}`);
    }
  }

  report.totalDays = MAX_DAYS;
  report.finalState = { ...state };
  printReport();
}

// ═══════════════════════════════════════════════════════
// Print Report
// ═══════════════════════════════════════════════════════
function printReport() {
  const state = report.finalState;
  console.log('\n');
  console.log('╔══════════════════════════════════════════════════════════╗');
  console.log('║           🎮 Crystal Cards — Play Report                ║');
  console.log('╚══════════════════════════════════════════════════════════╝');
  console.log(`\n📅 Duration: ${report.totalDays} days`);
  console.log(`🤖 Angela AI: ${report.angelaConnected ? 'Connected' : 'Offline'}`);

  console.log(`\n── Final State ──`);
  console.log(`❤️  HP: ${state.hp}/${state.maxHp}`);
  console.log(`🧠 Sanity: ${state.sanity}/100`);
  console.log(`💰 Gold: ${state.gold}`);
  console.log(`📖 Knowledge: ${state.knowledge}/100`);
  console.log(`📦 Board cards: ${state.boardCards.length}`);
  console.log(`📋 Sidebar cards: ${state.sidebarCards.length}`);
  console.log(`🎒 Inventory items: ${state.inventory.length}`);
  console.log(`🗺️  Unlocked: ${state.unlockedLocations.join(', ')}`);
  console.log(`🚩 Flags: ${Object.keys(state.flags).join(', ') || 'none'}`);

  console.log(`\n── Events ──`);
  const eventCounts = {};
  report.events.forEach(e => { eventCounts[e.type] = (eventCounts[e.type] || 0) + 1; });
  Object.entries(eventCounts).sort((a, b) => b[1] - a[1]).forEach(([type, count]) => {
    console.log(`  ${type}: ${count}`);
  });

  console.log(`\n── Combat Log ──`);
  if (report.combatLog.length === 0) {
    console.log('  No combat occurred');
  } else {
    report.combatLog.slice(-10).forEach(c => {
      console.log(`  Day ${c.day}: ${c.text}`);
    });
  }

  console.log(`\n── Dialogue Log ──`);
  if (report.dialogueLog.length === 0) {
    console.log('  No dialogue occurred');
  } else {
    report.dialogueLog.slice(-10).forEach(d => {
      console.log(`  Day ${d.day} [${d.character}]: ${d.text?.slice(0, 60) || d.dialogueId}`);
    });
  }

  console.log(`\n── Crafting ──`);
  if (report.craftingLog.length === 0) {
    console.log('  No crafting occurred');
  } else {
    report.craftingLog.forEach(c => {
      console.log(`  Day ${c.day}: ${c.recipe} → ${c.output}`);
    });
  }

  console.log(`\n── Bugs Found ──`);
  if (report.bugs.length === 0) {
    console.log('  ✅ No bugs detected');
  } else {
    report.bugs.forEach(b => {
      const icon = b.severity === 'critical' ? '🔴' : b.severity === 'high' ? '🟠' : '🟡';
      console.log(`  ${icon} [${b.severity}] ${b.description}`);
      if (b.context) console.log(`     Context: ${JSON.stringify(b.context)}`);
    });
  }

  console.log(`\n── Balance Issues ──`);
  if (report.balanceIssues.length === 0) {
    console.log('  ✅ No balance issues detected');
  } else {
    report.balanceIssues.forEach(b => {
      console.log(`  ⚠️  ${b}`);
    });
  }

  console.log(`\n── Decisions Summary ──`);
  const decisionCounts = {};
  report.decisions.forEach(d => {
    const key = d.decision?.action || 'unknown';
    decisionCounts[key] = (decisionCounts[key] || 0) + 1;
  });
  Object.entries(decisionCounts).sort((a, b) => b[1] - a[1]).forEach(([action, count]) => {
    console.log(`  ${action}: ${count} times`);
  });

  // Save report to file
  const reportPath = path.join(__dirname, 'play-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`\n📄 Full report saved to: ${reportPath}`);

  console.log('\n══════════════════════════════════════════════════════════');
  console.log('  Play report complete. Check play-report.json for details.');
  console.log('══════════════════════════════════════════════════════════');
}

// ═══════════════════════════════════════════════════════
// Run
// ═══════════════════════════════════════════════════════
runGame().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
