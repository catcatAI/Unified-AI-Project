#!/usr/bin/env node
const fs = require('fs');

const content = fs.readFileSync('game-data/cards.js', 'utf8');
const gc = JSON.parse(fs.readFileSync('../game-rpg/data/game_cards.json', 'utf8'));
const allCards = gc.cards || [];

const esc = s => (s || '').replace(/'/g, "\\'").replace(/[\n\r]/g, ' ').slice(0, 80);

// === NATIONAL CARDS ===
const nations = allCards.filter(c => c.card_type === '國家卡');
let nationEntries = nations.map(card => {
  const name = card.name.split('—')[0].split('（')[0].trim();
  const id = 'nation_' + name.replace(/\s+/g, '_').slice(0, 20);
  const desc = esc(card.description);
  const tokens = card.tokens || [];
  const govToken = tokens.find(t => t.name && t.name.includes('政體'));
  const gov = govToken ? govToken.value.slice(0, 40) : '未知政體';
  return `    { id: '${id}', name: '${esc(name)}', type: 'nation', icon: '🏴', desc: '${desc.slice(0,60)}', government: '${gov}' }`;
}).join(',\n');

// === ORGANIZATION CARDS ===
const orgs = allCards.filter(c => c.card_type === '組織卡');
let orgEntries = orgs.map(card => {
  const name = card.name.split('—')[0].trim();
  const id = 'org_' + name.replace(/\s+/g, '_').slice(0, 20);
  const desc = esc(card.description);
  return `    { id: '${id}', name: '${esc(name)}', type: 'organization', icon: '🏛️', desc: '${desc.slice(0,60)}' }`;
}).join(',\n');

// === RULE CARDS ===
const rules = allCards.filter(c => c.card_type === '規則卡');
let ruleEntries = rules.map(card => {
  const name = card.name.split('（')[0].trim();
  const id = 'rule_' + name.replace(/\s+/g, '_').slice(0, 20);
  const desc = esc(card.description);
  return `    { id: '${id}', name: '${esc(name)}', type: 'rule', icon: '📜', desc: '${desc.slice(0,60)}' }`;
}).join(',\n');

// === SCENE CARDS ===
const scenes = allCards.filter(c => c.card_type === '場景卡');
let sceneEntries = scenes.map(card => {
  const name = card.name.split('—')[0].trim();
  const id = 'scene_' + name.replace(/\s+/g, '_').slice(0, 20);
  const desc = esc(card.description);
  return `    { id: '${id}', name: '${esc(name)}', type: 'scene', icon: '🎬', desc: '${desc.slice(0,60)}' }`;
}).join(',\n');

// Find the end of the CARDS object (line with "};" before NPC_SCHEDULES)
const lines = content.split('\n');
// Find }; that ends CARDS (before '// World line descriptions')
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('World line descriptions')) {
    // Go backwards to find };
    for (let j = i - 1; j >= 0; j--) {
      if (lines[j].trim() === '};') {
        insertBefore = j;
        break;
      }
    }
    break;
  }
}

if (insertBefore === -1) {
  console.log('ERROR: Could not find end of CARDS object');
  process.exit(1);
}

// Build the new sections
const newSections = `
  // ═══════════════════════════════════════════════════════
  // National Cards (from game_cards.json)
  // ═══════════════════════════════════════════════════════
  nationalCards: [
${nationEntries}
  ],

  // ═══════════════════════════════════════════════════════
  // Organization Cards
  // ═══════════════════════════════════════════════════════
  organizationCards: [
${orgEntries}
  ],

  // ═══════════════════════════════════════════════════════
  // Rule Cards
  // ═══════════════════════════════════════════════════════
  ruleCards: [
${ruleEntries}
  ],

  // ═══════════════════════════════════════════════════════
  // Scene Cards
  // ═══════════════════════════════════════════════════════
  sceneCards: [
${sceneEntries}
  ],
`;

lines.splice(insertBefore, 0, newSections);

fs.writeFileSync('game-data/cards.js', lines.join('\n'), 'utf8');

console.log(`Added ${nations.length} national cards`);
console.log(`Added ${orgs.length} organization cards`);
console.log(`Added ${rules.length} rule cards`);
console.log(`Added ${scenes.length} scene cards`);
console.log('Done!');
