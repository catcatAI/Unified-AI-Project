#!/usr/bin/env node
const fs = require('fs');

const content = fs.readFileSync('game-data/cards.js', 'utf8');
const gc = JSON.parse(fs.readFileSync('../game-rpg/data/game_cards.json', 'utf8'));
const stories = gc.cards.filter(c => c.card_type === '劇情節點卡');

const esc = s => (s || '').replace(/'/g, "\\'").replace(/[\n\r]/g, ' ').slice(0, 80);

// Build story event entries
const entries = stories.map((card, i) => {
  const rawName = (card.name || '').split('—')[0].split('\n')[0].trim().slice(0, 30);
  const id = 'story_ep' + String(i + 1).padStart(2, '0');
  let desc = (card.description || '').replace(/[_]{3,}/g, '').trim();
  const sentences = desc.split(/[。\n]/).filter(s => s.trim().length > 5);
  desc = sentences[0] ? sentences[0].trim().slice(0, 60) : rawName;
  
  // Extract character associations from tokens
  const tokens = card.tokens || [];
  const charToken = tokens.find(t => t.name && (t.name.includes('角色') || t.name.includes('涉及')));
  const chars = charToken ? charToken.value.slice(0, 40) : '';

  return `    { id: '${id}', name: '${esc(rawName)}', type: 'story', icon: '📖', desc: '${esc(desc)}', characters: '${esc(chars)}' }`;
});

// Find insertion point: before the first };  after "World line descriptions"
const lines = content.split('\n');
let insertIdx = -1;
for (let i = 0; i < lines.length; i++) {
  if (lines[i].includes('World line descriptions')) {
    for (let j = i - 1; j >= 0; j--) {
      if (lines[j].trim() === '};') {
        insertIdx = j;
        break;
      }
    }
    break;
  }
}

if (insertIdx === -1) {
  console.log('ERROR: Could not find insertion point');
  process.exit(1);
}

const block = `
  // ═══════════════════════════════════════════════════════
  // Story Event Cards (from game_cards.json)
  // ═══════════════════════════════════════════════════════
  storyEvents: [
${entries.join(',\n')}
  ],
`;

lines.splice(insertIdx, 0, block);

fs.writeFileSync('game-data/cards.js', lines.join('\n'), 'utf8');
console.log(`Added ${stories.length} story event cards`);
