#!/usr/bin/env node
const fs = require('fs');

const content = fs.readFileSync('game-data/cards.js', 'utf8');
const gc = JSON.parse(fs.readFileSync('../game-rpg/data/game_cards.json', 'utf8'));
const allCards = gc.cards || [];

const inGameIds = new Set([
  'CC-01','CC-02','CC-17','CC-32','CC-37','CC-38','CC-39',
  'CC-49','CC-50','CC-51','CC-52','CC-53','CC-55','CC-57',
  'CC-58','CC-59','CC-61','CC-62',
]);

const locationMap = {
  'CC-03':'loc_mirror_lake','CC-04':'loc_witch_academy','CC-05':'loc_corridor',
  'CC-06':'loc_market','CC-07':'loc_library','CC-08':'loc_convenience_store',
  'CC-09':'loc_witch_academy','CC-10':'loc_holy_cross','CC-11':'loc_witch_academy',
  'CC-12':'loc_agriculture','CC-13':'loc_holy_cross','CC-14':'loc_forest',
  'CC-15':'loc_mirror_lake','CC-16':'loc_holy_cross','CC-18':'loc_mirror_lake',
  'CC-19':'loc_holy_cross','CC-20':'loc_mirror_lake','CC-21':'loc_library',
  'CC-22':'loc_library','CC-23':'loc_library','CC-24':'loc_corridor',
  'CC-25':'loc_witch_academy','CC-26':'loc_market','CC-27':'loc_convenience_store',
  'CC-28':'loc_holy_cross','CC-29':'loc_witch_academy','CC-30':'loc_holy_cross',
  'CC-31':'loc_corridor','CC-33':'loc_witch_academy','CC-34':'loc_witch_academy',
  'CC-35':'loc_library','CC-36':'loc_library','CC-40':'loc_library',
  'CC-41':'loc_library','CC-42':'loc_fog_islands','CC-43':'loc_rust_city',
  'CC-44':'loc_rust_city','CC-45':'loc_market','CC-46':'loc_witch_academy',
  'CC-47':'loc_corridor','CC-48':'loc_library','CC-54':'loc_frozen_wastes',
  'CC-56':'loc_orbital_station','CC-60':'loc_market','CC-63':'loc_abandoned_mine',
  'CC-64':'loc_abandoned_mine','CC-65':'loc_abandoned_mine','CC-66':'loc_mirror_lake',
  'CC-67':'loc_mirror_lake','CC-68':'loc_corridor','CC-69':'loc_corridor',
  'CC-70':'loc_market','CC-71':'loc_market',
};

const missing = allCards.filter(c =>
  c.card_id && /^CC-\d+$/.test(c.card_id) && !inGameIds.has(c.card_id)
);

console.log(`Processing ${missing.length} characters...`);

const esc = s => s.replace(/'/g, "\\'").replace(/[\n\r]/g, ' ');

// Build character entries
const charEntries = missing.map(card => {
  const ccNum = card.card_id;
  const rawName = card.name.split('(')[0].split('（')[0].trim();
  const id = 'char_cc' + ccNum.replace('CC-', '');
  const raceToken = (card.tokens || []).find(t => t.type === 'race');
  const race = raceToken ? raceToken.value.slice(0, 40) : '未知';
  const role = (card.stats || {})['role定位'] || race;
  const abs = (card.abilities || []).slice(0, 3).map(a => a.name);
  let desc = (card.description || '').replace(/[_]{3,}/g, '').trim();
  const sentences = desc.split(/[。\n]/).filter(s => s.trim().length > 5);
  desc = sentences[0] ? sentences[0].trim().slice(0, 60) : rawName;
  const hp = 70 + Math.floor(Math.random() * 50);
  const atk = 4 + Math.floor(Math.random() * 12);
  const def = 3 + Math.floor(Math.random() * 10);
  const spd = 4 + Math.floor(Math.random() * 12);
  const loc = locationMap[ccNum] || 'loc_holy_cross';
  const dlgId = `greeting_${id}`;

  return `      { id: '${id}', name: '${esc(rawName)}', type: 'character', color: '#7B1FA2', icon: '👤', role: '${esc(role).slice(0,40)}', race: '${esc(race).slice(0,40)}', desc: '${esc(desc)}', stats: { hp: ${hp}, atk: ${atk}, def: ${def}, spd: ${spd} }, abilities: ${JSON.stringify(abs)}, dialogue: '${dlgId}', location: '${loc}' },`
});

// Build dialogue entries
const dlgEntries = [];
missing.forEach(card => {
  const ccNum = card.card_id;
  const rawName = card.name.split('(')[0].split('（')[0].trim();
  const id = 'char_cc' + ccNum.replace('CC-', '');
  const raceToken = (card.tokens || []).find(t => t.type === 'race');
  const race = raceToken ? raceToken.value.slice(0, 40) : '未知';
  let desc = (card.description || '').replace(/[_]{3,}/g, '').trim();
  const sentences = desc.split(/[。\n]/).filter(s => s.trim().length > 5);
  desc = sentences[0] ? sentences[0].trim().slice(0, 60) : rawName;
  const dlgId = `greeting_${id}`;

  dlgEntries.push(`    ${dlgId}: { speaker: '${esc(rawName)}', text: '${esc(desc).slice(0,60)}', choices: [{ text: '你是誰？', next: '${id}_who' }, { text: '離開', next: null }] },`);
  dlgEntries.push(`    ${id}_who: { speaker: '${esc(rawName)}', text: '「我叫${esc(rawName)}。${esc(race).slice(0,30)}。」', choices: [{ text: '知道了', next: null }] },`);
});

// Find exact insertion points
// 1. Characters: find the line "  ]," before "dialogues: {"
const lines = content.split('\n');
let charInsertIdx = -1;
let dlgInsertIdx = -1;

for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('characters: [')) {
    // Found characters array start — go forward to find ],
    let depth = 1;
    for (let j = i + 1; j < lines.length; j++) {
      if (lines[j].includes('[')) depth++;
      if (lines[j].includes(']')) depth--;
      if (depth === 0) {
        charInsertIdx = j;  // Insert BEFORE the ],
        break;
      }
    }
    break;
  }
}

// 2. Dialogues: find end of dialogues section
// Search for the last dialogue entry (ending with },) before the first }; 
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('dialogues: {')) {
    // Found dialogues start — go forward to find the }, that closes it
    let depth = 1;
    for (let j = i + 1; j < lines.length; j++) {
      if (lines[j].includes('{')) depth++;
      if (lines[j].includes('}')) depth--;
      if (depth === 0) {
        dlgInsertIdx = j;  // This is the }, closing dialogues
        break;
      }
    }
    break;
  }
}

console.log(`Characters insert at line: ${charInsertIdx}`);
console.log(`Dialogues insert at line: ${dlgInsertIdx}`);

if (charInsertIdx === -1 || dlgInsertIdx === -1) {
  console.log('ERROR: Could not find insertion points');
  console.log('Lines around dialogues:');
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('dialogues:')) {
      for (let j = Math.max(0,i-5); j < Math.min(lines.length, i+5); j++) {
        console.log(`  ${j+1}: ${lines[j].slice(0,80)}`);
      }
      break;
    }
  }
  process.exit(1);
}

// Insert dialogues first (higher line number), then characters (lower)
const charBlock = charEntries.join('\n') + '\n';
const dlgBlock = dlgEntries.join('\n') + '\n';

lines.splice(dlgInsertIdx, 0, dlgBlock);
lines.splice(charInsertIdx, 0, charBlock);

fs.writeFileSync('game-data/cards.js', lines.join('\n'), 'utf8');
console.log(`Done! Added ${missing.length} characters + ${dlgEntries.length} dialogues`);
