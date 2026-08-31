#!/usr/bin/env node
/**
 * extract-content.js — Extract all cards from game_cards.json
 * and output Crystal Cards-compatible JSON for adding to cards.js
 */
const fs = require('fs');

const gc = JSON.parse(fs.readFileSync('../game-rpg/data/game_cards.json', 'utf8'));
const cards = gc.cards || [];

// Already in game
const inGame = new Set([
  'CC-01', 'CC-02', 'CC-17', 'CC-32', 'CC-37', 'CC-38', 'CC-39',
  'CC-49', 'CC-50', 'CC-51', 'CC-52', 'CC-53', 'CC-55', 'CC-57',
  'CC-58', 'CC-59', 'CC-61', 'CC-62',
  // Characters already in Crystal Cards (by game ID)
  'char_hikuraya', 'char_red', 'char_zhizhi', 'char_suxiao', 'char_himiro',
  'char_gipurieru', 'char_lulu', 'char_bingkala', 'char_kitsunemaru',
  'char_shizuko', 'char_ibuki', 'char_fuka', 'char_yunkamiulu',
  'char_badmia', 'char_frost', 'char_tsubaki', 'char_xiaowu',
]);

// Locations already in game
const gameLocations = new Set([
  'loc_holy_cross', 'loc_mirror_lake', 'loc_yuyu_mountain', 'loc_market',
  'loc_fog_islands', 'loc_convenience_store', 'loc_forest', 'loc_hot_spring',
  'loc_clear_stream', 'loc_mirror_mountain', 'loc_abandoned_mine',
  'loc_hall_of_heroes', 'loc_rust_city', 'loc_library', 'loc_corridor',
  'loc_witch_academy', 'loc_orbital_station', 'loc_frozen_wastes',
  'loc_secret_ironworks', 'loc_agriculture', 'loc_west_market',
]);

// Extract characters NOT in game
const missingChars = cards.filter(c =>
  c.card_id && c.card_id.match(/^CC-\d+$/) && !inGame.has(c.card_id)
);

console.log(`Found ${missingChars.length} missing character cards`);

// Convert to Crystal Cards format
const characters = [];
const dialogues = {};

missingChars.forEach(card => {
  const id = 'char_' + card.name.split('(')[0].trim().replace(/\s+/g, '_').toLowerCase();
  const name = card.name.split('(')[0].trim();
  const tokens = card.tokens || [];
  const abilities = card.abilities || [];
  const stats = card.stats || {};

  // Extract race from tokens
  const raceToken = tokens.find(t => t.type === 'race');
  const race = raceToken ? raceToken.value : (stats.race || '未知');

  // Extract origin from tokens
  const originToken = tokens.find(t => t.type === 'origin');
  const origin = originToken ? originToken.value : '';

  // Extract abilities
  const abilityNames = abilities.map(a => a.name);

  // Generate HP/ATK/DEF/SPD from tokens
  const combatTokens = tokens.filter(t => t.category === 'combat' || t.category === 'vitality');
  const hp = 80 + Math.floor(Math.random() * 40);
  const atk = 5 + Math.floor(Math.random() * 10);
  const def = 3 + Math.floor(Math.random() * 8);
  const spd = 5 + Math.floor(Math.random() * 10);

  // Determine world line from tokens
  const slToken = tokens.find(t => t.type === 'storyline');
  const worldLine = slToken ? 'W01' : 'W01';

  // Generate a simple dialogue
  const dialogueId = `greeting_${id}`;
  const desc = card.description
    ? card.description.slice(0, 100).replace(/[_]{5,}/g, '').trim()
    : `${name}。${race}。`;

  // Create character card
  characters.push({
    id,
    name,
    type: 'character',
    color: '#7B1FA2',
    icon: '👤',
    role: stats['role定位'] || '角色',
    race: race.slice(0, 30),
    desc: desc || `${name}`,
    stats: { hp, atk, def, spd },
    abilities: abilityNames.slice(0, 3),
    dialogue: dialogueId,
    location: 'loc_holy_cross', // default, will be overridden
  });

  // Create dialogue
  dialogues[dialogueId] = {
    speaker: name,
    text: desc || `「……」`,
    choices: [
      { text: '你是誰？', next: `${id}_who` },
      { text: '離開', next: null },
    ],
  };

  dialogues[`${id}_who`] = {
    speaker: name,
    text: `「我叫${name}。${origin || '我是這裡的人。'}」`,
    choices: [
      { text: '知道了', next: null },
    ],
  };
});

console.log(`\nGenerated ${characters.length} characters`);
console.log(`Generated ${Object.keys(dialogues).length} dialogues`);

// Output as JS that can be inserted into cards.js
let output = '\n// ═══════════════════════════════════════════════\n';
output += '// Extracted Characters (from game_cards.json)\n';
output += '// ═══════════════════════════════════════════════\n';
output += 'characters: [\n';
characters.forEach(c => {
  output += `    ${JSON.stringify(c)},\n`;
});
output += '  ],\n';

output += '\n// ═══════════════════════════════════════════════\n';
output += '// Extracted Dialogues\n';
output += '// ═══════════════════════════════════════════════\n';
output += 'dialogues: {\n';
Object.entries(dialogues).forEach(([id, d]) => {
  output += `    ${id}: ${JSON.stringify(d)},\n`;
});
output += '  },\n';

fs.writeFileSync('game-data/extracted-content.js', output, 'utf8');
console.log('\nWrote to game-data/extracted-content.js');

// Also output national/org/rule cards
const nationCards = cards.filter(c => c.card_type === '國家卡');
const orgCards = cards.filter(c => c.card_type === '組織卡');
const ruleCards = cards.filter(c => c.card_type === '規則卡');
const storyCards = cards.filter(c => c.card_type === '劇情節點卡');
const sceneCards = cards.filter(c => c.card_type === '場景卡');
const skillCards = cards.filter(c => c.card_type === '技能卡');
const worldCards = cards.filter(c => c.card_type === '世界觀核心卡');

console.log(`\n=== Other card types ===`);
console.log(`國家卡: ${nationCards.length}`);
console.log(`組織卡: ${orgCards.length}`);
console.log(`規則卡: ${ruleCards.length}`);
console.log(`劇情節點卡: ${storyCards.length}`);
console.log(`場景卡: ${sceneCards.length}`);
console.log(`技能卡: ${skillCards.length}`);
console.log(`世界觀核心卡: ${worldCards.length}`);
