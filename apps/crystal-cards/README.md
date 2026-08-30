# Crystal Cards 💎

Stacklands-style card game set in the Angela Matrix world.

## Features

- **Stacklands gameplay**: Drag cards, stack to craft, explore locations, fight enemies
- **Crystal card design**: Glassmorphism frosted glass cards with color-coded types
- **Rich world content**: 10+ locations, 5+ characters, 10+ items, 5+ enemies from game-rpg
- **Story system**: Branching dialogues with choices, skill checks, and consequences
- **Sound effects**: Procedural audio via Web Audio API (no external files needed)
- **Settings**: Volume, language, quality, tutorial toggle

## Card Types

| Color | Type | Example |
|-------|------|---------|
| 🔵 Blue | Location | 聖十字校園, 鏡湖, 迴廊 |
| 🟣 Purple | Character | 晞咕萊雅, 紅, 守門人 |
| 🟢 Green | Item | 手電筒, 迴廊鑰匙, 水晶 |
| 🟡 Yellow | Resource | 木材, 草藥, 金幣 |
| 🔴 Red | Enemy | 暗影, 腐化體, 迴音 |

## Development

```bash
# Install dependencies
pnpm install

# Run in development
pnpm start
# or
npx electron . --no-sandbox
```

## Build

```bash
# Build for current platform
pnpm run build:linux   # Linux AppImage + deb
pnpm run build:win     # Windows NSIS installer + portable
pnpm run build:all     # Both
```

Output will be in `dist/` directory.

## Architecture

```
apps/crystal-cards/
├── src/
│   ├── main.js          # Electron main process
│   ├── preload.js       # Electron preload (settings IPC)
│   ├── index.html       # Game UI structure
│   ├── style.css        # Crystal glassmorphism styles
│   ├── game-engine.js   # Core game loop, card management, crafting
│   ├── renderer.js      # DOM rendering, drag-drop, sidebar
│   ├── dialog.js        # Story/dialogue system
│   └── sounds.js        # Procedural sound effects (Web Audio)
├── data/
│   └── cards.js         # Game content (extracted from game-rpg)
├── assets/
│   ├── icons/           # App icons
│   └── sounds/          # (Reserved for future sound files)
├── package.json
└── .gitignore
```

## Content Source

All game content (locations, characters, items, enemies, dialogues) is extracted from:
- `apps/game-rpg/game_data.py` — NPC generation, item catalogs, world settings
- `apps/game-rpg/game.py` — Story scenes, choices, skill checks
- Angela AI project world setting (W01-W04 world lines, 迴廊, etc.)

## Credits

- Game content: Angela AI project (game-rpg)
- Card rendering: CSS Glassmorphism
- Sound: Web Audio API procedural generation
