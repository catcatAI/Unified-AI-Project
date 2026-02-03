import { GameState, MValue, CharacterStats } from '../types';
import { Type, FunctionDeclaration } from "@google/genai";

// --- JSON Schema from types.ts ---
// By converting the types to a schema at runtime, types.ts remains the single source of truth.
const mValues: MValue[] = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6'];
const statsKeys: (keyof CharacterStats)[] = ["maxHp", "hp", "maxMp", "mp", "maxStamina", "stamina", "strength", "agility", "intelligence", "maxM3LogicStress", "m3LogicStress", "maxM6SecurityShield", "m6SecurityShield"];

const subItemSchema = {
    type: Type.OBJECT,
    properties: {
        id: { type: Type.STRING, description: "Unique ID, only needed when removing an item." },
        name: { type: Type.STRING },
        description: { type: Type.STRING },
        quantity: { type: Type.INTEGER },
        mValueProfile: { type: Type.ARRAY, items: { type: Type.STRING, enum: mValues } },
        iconGenerationPrompt: { type: Type.STRING }
    },
    required: ["name", "description", "quantity"]
};

const statsSchemaProperties = {
    ...Object.fromEntries(
        statsKeys.map(key => [key, { type: Type.NUMBER, description: `The character's ${key} stat.` }])
    ),
};

const characterSchema = {
    type: Type.OBJECT,
    properties: {
        name: { type: Type.STRING },
        description: { type: Type.STRING },
        gender: { type: Type.STRING, enum: ['male', 'female', 'other'] },
        inventory: { type: Type.ARRAY, items: subItemSchema },
        stats: { type: Type.OBJECT, properties: statsSchemaProperties, required: ["maxHp", "hp"] }
    },
    required: ["name", "description", "gender", "stats"]
};

export const setupResponseSchema = {
    type: Type.OBJECT,
    properties: {
        playerCharacter: characterSchema,
        aiCharacters: { type: Type.ARRAY, items: characterSchema },
        openingScene: { type: Type.STRING },
        gameSummary: { type: Type.STRING },
        genreAndTone: { type: Type.STRING },
        startingLocation: { type: Type.STRING },
        suggestedActions: { type: Type.ARRAY, items: { type: Type.STRING } },
        partyStash: { type: Type.ARRAY, items: subItemSchema },
        vehicles: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { id: { type: Type.STRING }, name: { type: Type.STRING }, description: { type: Type.STRING }, inventory: { type: Type.ARRAY, items: subItemSchema } }, required: ["id", "name"] } },
        realEstate: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { id: { type: Type.STRING }, name: { type: Type.STRING }, description: { type: Type.STRING } }, required: ["id", "name"] } },
        locationItems: { type: Type.ARRAY, items: subItemSchema },
        knownLocations: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { id: { type: Type.STRING }, name: { type: Type.STRING }, description: { type: Type.STRING } }, required: ["id", "name"] } },
        mapImagePrompt: { type: Type.STRING },
        locationImagePrompt: { type: Type.STRING },
        map: {
            type: Type.OBJECT,
            properties: {
                currentMap: { type: Type.STRING },
                width: { type: Type.INTEGER },
                height: { type: Type.INTEGER },
                tiles: { type: Type.ARRAY, items: { type: Type.ARRAY, items: { type: Type.STRING } } },
                playerX: { type: Type.INTEGER },
                playerY: { type: Type.INTEGER },
                playerDirection: { type: Type.STRING, enum: ['up', 'down', 'left', 'right'] },
                objects: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { id: { type: Type.STRING }, name: { type: Type.STRING }, x: { type: Type.INTEGER }, y: { type: Type.INTEGER }, icon: { type: Type.STRING } }, required: ["id", "name", "x", "y", "icon"] } }
            },
            required: ["width", "height", "tiles", "playerX", "playerY"]
        }
    },
    required: ["playerCharacter", "aiCharacters", "openingScene", "gameSummary", "genreAndTone", "startingLocation", "suggestedActions"]
};


export const playerActionResponseSchema = { 
    type: Type.OBJECT, 
    properties: { 
        newGameLogSummary: { type: Type.STRING, description: "A new, single-paragraph summary of the game state after this turn." }, 
        interpretedPlayerAction: { type: Type.STRING, description: "A rephrasing of the player's action from the GM's perspective. Only use this if Character Agency is enabled and the action is ambiguous." }, 
        aiActions: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { characterName: { type: Type.STRING }, action: { type: Type.STRING }, dialogue: { type: Type.STRING } }, required: ["characterName", "action"] } }, 
        gmNarrative: { type: Type.STRING, description: "The main narration describing the outcome of all actions. This is the primary story content. Can include tags like [SFX: explosion] or [CINEMATIC: a dragon flying over the mountains]." }, 
        statChanges: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { characterName: { type: Type.STRING }, stat: { type: Type.STRING, enum: statsKeys }, change: { type: Type.NUMBER } }, required: ["characterName", "stat", "change"] } }, 
        inventoryChanges: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { type: { type: Type.STRING, enum: ['add', 'remove'] }, target: { type: Type.OBJECT, properties: { type: { type: Type.STRING, enum: ['player', 'character', 'stash', 'ground', 'vehicle'] }, name: { type: Type.STRING, description: "Required if type is 'character'." }, id: { type: Type.STRING, description: "Required if type is 'vehicle'." }, }, required: ['type'] }, item: subItemSchema }, required: ["type", "target", "item"] } },
        characterChanges: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { type: { type: Type.STRING, enum: ['add', 'remove'] }, character: { type: Type.OBJECT, properties: { name: { type: Type.STRING }, description: { type: Type.STRING }, gender: {type: Type.STRING, enum: ['male', 'female', 'other']}, 
            inventory: {type: Type.ARRAY, items: subItemSchema },
            stats: { type: Type.OBJECT, properties: statsSchemaProperties, required: ["maxHp", "hp"] }
        }, required: ["name"] } }, required: ["type", "character"] } },
        vehicleChanges: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { type: { type: Type.STRING, enum: ['add', 'remove'] }, vehicle: { type: Type.OBJECT, properties: { id: { type: Type.STRING }, name: { type: Type.STRING }, description: { type: Type.STRING }, 
            inventory: { type: Type.ARRAY, items: subItemSchema }
        }, required: ["id", "name"] } }, required: ["type", "vehicle"] } },
        realEstateChanges: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { type: { type: Type.STRING, enum: ['add', 'remove'] }, property: { type: Type.OBJECT, properties: { id: { type: Type.STRING }, name: { type: Type.STRING }, description: { type: Type.STRING } }, required: ["id", "name"] } }, required: ["type", "property"] } },
        knownLocations: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { id: { type: Type.STRING }, name: { type: Type.STRING }, description: { type: Type.STRING } }, required: ["id", "name"] } },
        location: { type: Type.STRING, description: "The new location name, if the party has moved." },
        gameMode: { type: Type.STRING, enum: ['narrative', 'action', 'simulation', 'puzzle'], description: "Change the game mode if the situation demands it (e.g., to 'action' for combat)." },
        activeEnemies: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { name: { type: Type.STRING }, hp: { type: Type.INTEGER }, maxHp: { type: Type.INTEGER }, description: { type: Type.STRING } }, required: ["name", "hp", "maxHp"] } },
        resources: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { resourceName: { type: Type.STRING }, quantity: { type: Type.INTEGER } }, required: ["resourceName", "quantity"] } },
        suggestedActions: { type: Type.ARRAY, items: { type: Type.STRING } },
        summonChallenge: { type: Type.OBJECT, properties: { sequence: { type: Type.ARRAY, items: { type: Type.STRING } }, timeLimit: { type: Type.INTEGER } }, required: ["sequence", "timeLimit"] },
        tile_changes: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { x: { type: Type.INTEGER }, y: { type: Type.INTEGER }, tile: { type: Type.STRING } }, required: ["x", "y", "tile"] } },
        map_object_changes: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { type: { type: Type.STRING, enum: ['add', 'remove'] }, object: { type: Type.OBJECT, properties: { id: { type: Type.STRING }, name: { type: Type.STRING }, x: { type: Type.INTEGER }, y: { type: Type.INTEGER }, icon: { type: Type.STRING } }, required: ["id", "name", "x", "y", "icon"] } }, required: ["type", "object"] } },
        m2ChaosNarrative: { type: Type.STRING, description: "A minor, non-deterministic but safe behavioral variation used only in M6 mode to add narrative flavor." }
    }, 
    required: ["newGameLogSummary", "aiActions", "gmNarrative"] 
};


// Tool definition for the AI to retrieve past events.
export const generateSearchQueriesTool: FunctionDeclaration = {
  name: 'generate_search_queries',
  description: "If you need to recall details about past events, characters, or locations to accurately respond to the player's action, generate a list of search queries to retrieve that information from the game log. If no extra information is needed, return an empty list.",
  parameters: {
    type: Type.OBJECT,
    properties: {
      queries: {
        type: Type.ARRAY,
        items: { type: Type.STRING },
        description: 'A list of keywords or phrases to search for in the game history (e.g., ["old man quest", "Whispering Cave key"]). Return an empty array if no search is needed.',
      },
    },
    required: ['queries'],
  },
};


/**
 * Builds a structured, high-density context string for the AI based on the current game state and active M-Core mode.
 * This function implements the core logic of the CMOS (Context & Memory Orchestration System).
 * @param gameState The current state of the game.
 * @param mCore The active M-Core mode ('M1', 'M3', or 'M6'), which influences the context depth.
 * @returns A formatted string containing the full context for the AI prompt.
 */
export function buildPromptContext(gameState: GameState, mCore: 'M1' | 'M3' | 'M6'): string {
    // I. 摘要链 (Context Chain) - A summary of recent events.
    const historySlice = mCore === 'M1' ? -4 : -8;
    const recentHistory = gameState.gameLog.slice(historySlice).map(m => {
        const author = m.isGM ? "GM" : m.author;
        const content = m.interpretedPlayerAction || m.dialogue || m.content;
        return `${author}: ${content}`;
    }).join('\n');
    const contextChain = `**Recent Events:**\n${recentHistory}`;

    // II. 记忆库 (Knowledge Base) - Key facts from the game state.
    const player = gameState.characters.find(c => !c.isAI);
    const knowledgeBase = `
**Key Facts:**
- Player: ${player?.name} (HP: ${player?.stats.hp}/${player?.stats.maxHp}, MP: ${player?.stats.mp}/${player?.stats.maxMp}, SP: ${player?.stats.stamina}/${player?.stats.maxStamina}, M3 Stress: ${player?.stats.m3LogicStress || 0}, M6 Shield: ${player?.stats.m6SecurityShield || 0})
- Location: ${gameState.location}
- Party Members: ${gameState.characters.filter(c => c.isAI).map(c => c.name).join(', ') || 'None'}
- Game Summary: ${gameState.gameSummary}
- Game Style: ${gameState.gameStyle}
- Current Mode: ${gameState.gameMode}
    `;
    
    // In M3 or M6 mode, we can add more detailed context.
    let detailedKnowledge = '';
    if (mCore === 'M3' || mCore === 'M6') {
        const inventoryString = (inv: any) => Array.isArray(inv) ? (inv.map(item => `- ${item.name} (x${item.quantity})`).join('\n') || 'Empty') : 'Empty';

        detailedKnowledge = `
**Player Inventory:**
${inventoryString(player?.inventory)}

**Items on Ground:**
${inventoryString(gameState.locationItems)}
        `;
    }

    // The policy stack is handled by the system instruction in cognitiveEngineService.
    // This function assembles the content part of the prompt.
    return `${contextChain}\n\n${knowledgeBase}\n${detailedKnowledge}`;
}