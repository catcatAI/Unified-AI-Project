import { GameState, PlayerActionSuccessResult, DiceRoll, Character, Cinematic, Sfx, InventoryContainer, GlobalCodex } from '../types';
import { charactersReducer } from '../reducers/charactersReducer';
import { inventoryReducer } from '../reducers/inventoryReducer';
import { mapReducer } from '../reducers/mapReducer';
import { gameLogReducer } from '../reducers/gameLogReducer';
import { miscReducer } from '../reducers/miscReducer';
import { produce } from 'immer';

// --- Save File Migration Logic ---
export const migrateGameState = (gameState: any): GameState => {
  // Check if migration is needed by looking for old properties
  const needsMigration = gameState.characters?.some((c: any) => c.imageUrl !== undefined) 
    || gameState.mapImageUrl !== undefined
    || gameState.gameLog?.some((m: any) => m.cinematic?.url || m.sfx?.url);

  if (!needsMigration) {
    return gameState as GameState;
  }
  
  console.log("Migrating old save file format...");

  return produce(gameState, (draft: any) => {
    draft.assetCache = draft.assetCache || {};
    
    // Characters & their Items
    if(draft.characters) {
        draft.characters.forEach((char: any) => {
          if (char.imageUrl) {
            const key = `portrait-${char.name}`;
            char.portraitAssetKey = key;
            draft.assetCache[key] = char.imageUrl;
            delete char.imageUrl;
          }
          if(char.inventory) {
              char.inventory.forEach((item: any) => {
                if (item.iconUrl) {
                  const key = `icon-${item.name.toLowerCase().replace(/\s+/g, '-')}`;
                  item.iconAssetKey = key;
                  draft.assetCache[key] = item.iconUrl;
                  delete item.iconUrl;
                }
              });
          }
        });
    }
    
    // Global map & location
    if (draft.mapImageUrl) {
      draft.mapAssetKey = 'world-map';
      draft.assetCache[draft.mapAssetKey] = draft.mapImageUrl;
      delete draft.mapImageUrl;
    }
    if (draft.locationImageUrl) {
      draft.locationAssetKey = `location-${draft.location?.replace(/\s+/g, '-') || 'unknown'}`;
      draft.assetCache[draft.locationAssetKey] = draft.locationImageUrl;
      delete draft.locationImageUrl;
    }
    
    // Cinematics & SFX in game log
    if (draft.gameLog) {
        draft.gameLog.forEach((msg: any) => {
            if (msg.cinematic && msg.cinematic.url) {
                const key = `cinematic-${msg.id}`;
                msg.cinematic.assetKey = key;
                draft.assetCache[key] = msg.cinematic.url;
                delete msg.cinematic.url;
            }
            if (msg.sfx && msg.sfx.url) {
                const key = `sfx-${msg.id}`;
                msg.sfx.assetKey = key;
                draft.assetCache[key] = msg.sfx.url;
                delete msg.sfx.url;
            }
        });
    }

  }) as GameState;
};

// --- Dice Roll Logic (moved from gameLogReducer) ---

function parseDiceRoll(rollString: string): { numDice: number; dieType: number; modifier: number } {
    const match = rollString.match(/(\d+)?d(\d+)([+-]\d+)?/);
    if (!match) return { numDice: 1, dieType: 20, modifier: 0 };
    return {
        numDice: parseInt(match[1] || '1', 10),
        dieType: parseInt(match[2], 10),
        modifier: parseInt(match[3] || '0', 10),
    };
}

function calculateDiceRoll(rollString: string): number {
    const { numDice, dieType, modifier } = parseDiceRoll(rollString);
    let totalRoll = 0;
    for (let i = 0; i < numDice; i++) {
        totalRoll += Math.floor(Math.random() * dieType) + 1;
    }
    return totalRoll + modifier;
}

function handleDiceRollCombat(draft: GameState, roll: DiceRoll, gmName: string) {
    const attacker = draft.characters.find(c => c.name === roll.characterName);
    const targetEnemyIndex = draft.activeEnemies.findIndex(e => e.name === roll.targetName);

    if (attacker && targetEnemyIndex > -1) {
        const targetEnemy = draft.activeEnemies[targetEnemyIndex];
        
        // The result is now pre-calculated, so we just use it.
        const actualRoll = roll.result;

        let baseDamage = attacker.stats.strength;
        let multiplier = 1.0;
        let successText = "hits";

        switch (roll.successLevel) {
            case 'critical_success': multiplier = 2.0; successText = "critically hits"; break;
            case 'success': multiplier = 1.0; successText = "hits"; break;
            case 'failure': multiplier = 0.0; successText = "misses"; break;
            case 'critical_failure': multiplier = 0.0; successText = "critically misses"; break;
        }

        const finalDamage = Math.round(baseDamage * multiplier);
        const newHp = Math.max(0, targetEnemy.hp - finalDamage);
        targetEnemy.hp = newHp;

        let combatMessageContent = `${attacker.name} ${successText} ${targetEnemy.name} for ${finalDamage} damage (Roll: ${roll.result}, ${roll.successLevel.replace('_', ' ')}).`;
        
        if (newHp > 0) {
            combatMessageContent += ` (${targetEnemy.name} HP: ${newHp}/${targetEnemy.maxHp})`;
        } else {
            combatMessageContent += `\n${targetEnemy.name} has been defeated!`;
        }
        
        gameLogReducer(draft, { type: 'ADD_SYSTEM_MESSAGE_TO_LOG', payload: { id: `msg-combat-${Date.now()}`, content: combatMessageContent, diceRoll: roll } });

        const aliveEnemies = draft.activeEnemies.filter(e => e.hp > 0);
        if (aliveEnemies.length < draft.activeEnemies.length) {
            draft.activeEnemies = aliveEnemies;
        }

        if (draft.activeEnemies.length === 0 && draft.gameMode === 'action') {
            draft.gameMode = 'narrative';
            draft.gameLog.push({ id: `msg-combat-end-${Date.now()}`, author: gmName, content: "Combat has ended.", isGM: true });
        }
    } else {
        // This case might happen if AI specifies a combat roll for a non-existent enemy. Log it as a system message.
        gameLogReducer(draft, { type: 'ADD_SYSTEM_MESSAGE_TO_LOG', payload: { id: `msg-dice-${Date.now()}`, content: '', diceRoll: roll } });
    }
}


// --- Main Service Function ---

type ProcessAiTurnPayload = {
    result: PlayerActionSuccessResult;
    gmName: string;
    settings: {
        roundRobinInitiative: boolean;
        characterAgency: boolean;
    };
};

/**
 * The main processing function for an AI's turn result.
 * It takes an Immer draft and the raw AI response payload, and applies all
 * game logic and state changes to the draft.
 * This function is NOT pure and is designed to be used within a produce() call.
 */
export function processAiTurn(draft: GameState, payload: ProcessAiTurnPayload) {
    const { result, gmName, settings } = payload; 
    const timestamp = Date.now();

    if (settings.characterAgency && typeof result.interpretedPlayerAction === 'string' && result.interpretedPlayerAction.trim()) {
        gameLogReducer(draft, { type: 'UPDATE_LAST_PLAYER_MESSAGE_INTERPRETATION', payload: result.interpretedPlayerAction });
    }

    if (Array.isArray(result.aiActions)) {
        result.aiActions.forEach((aiAction, index: number) => {
            if (!aiAction || typeof aiAction.characterName !== 'string' || typeof aiAction.action !== 'string') {
                console.warn('Invalid AI Action object received:', aiAction);
                return;
            }
            if (aiAction.action || aiAction.dialogue) {
                gameLogReducer(draft, { type: 'ADD_AI_ACTION_TO_LOG', payload: { id: `msg-ai-${timestamp}-${index}`, characterName: aiAction.characterName, action: aiAction.action, dialogue: aiAction.dialogue } });
            }
        });
    }
    
    if (result.m2ChaosNarrative) {
         gameLogReducer(draft, { type: 'ADD_GM_NARRATIVE_TO_LOG', payload: { id: `msg-gm-m2-${timestamp}`, gmName: gmName, content: result.m2ChaosNarrative }});
    }

    const gmNarrative = (typeof result.gmNarrative === 'string') ? result.gmNarrative.trim() : '';
    if (gmNarrative) {
        const gmMessageId = `msg-gm-${timestamp}`;
        const sfxRegex = /\[SFX:([^\]]+)\]/g;
        const cinematicRegex = /\[CINEMATIC:([^\]]+)\]/g;
        let cinematic: Cinematic | undefined;
        let sfx: Sfx | undefined;

        sfxRegex.lastIndex = 0;
        cinematicRegex.lastIndex = 0;

        const sfxMatch = sfxRegex.exec(gmNarrative);
        if (sfxMatch && sfxMatch[1]) sfx = { prompt: sfxMatch[1].trim(), status: 'pending' };
        const cinematicMatch = cinematicRegex.exec(gmNarrative);
        if (cinematicMatch && cinematicMatch[1]) cinematic = { type: 'image', prompt: cinematicMatch[1].trim(), status: 'pending' };
        
        gameLogReducer(draft, { type: 'ADD_GM_NARRATIVE_TO_LOG', payload: { id: gmMessageId, gmName, content: gmNarrative, cinematic, sfx } });
    }

    if (result.diceRoll) {
        // Always calculate the roll result so it's available for logging or combat.
        result.diceRoll.result = calculateDiceRoll(result.diceRoll.roll);

        if (/attack|strike|hit|cast|shoot|swing/i.test(result.diceRoll.action)) {
            handleDiceRollCombat(draft, result.diceRoll, gmName);
        } else {
            gameLogReducer(draft, { type: 'ADD_SYSTEM_MESSAGE_TO_LOG', payload: { id: `msg-dice-${timestamp}`, content: '', diceRoll: result.diceRoll } });
        }
    }

    if (Array.isArray(result.statChanges)) {
        result.statChanges.forEach((change) => {
            if (!change || typeof change.characterName !== 'string' || typeof change.stat !== 'string' || typeof change.change !== 'number' || !Number.isFinite(change.change)) {
                console.warn('Invalid or malformed statChange object received from AI, skipping:', change);
                return;
            }
            charactersReducer(draft, { type: 'UPDATE_CHARACTER_STATS', payload: { charName: change.characterName, stat: change.stat as any, change: change.change } });
        });
    }

    if (Array.isArray(result.inventoryChanges)) {
        result.inventoryChanges.forEach((change) => {
            const target = change.target as any;
            if (!change || !change.type || !target || !change.item || typeof change.item.name !== 'string' || typeof change.item.quantity !== 'number') {
                console.warn('Invalid inventoryChange object received:', change);
                return;
            }
            if ( (target.type === 'character' && typeof target.name !== 'string') || (target.type === 'vehicle' && typeof target.id !== 'string') ) {
                console.warn('Invalid inventoryChange target object received:', target);
                return;
            }

            if (change.type === 'add') {
                inventoryReducer(draft, { type: 'ADD_ITEM_TO_INVENTORY', payload: { owner: change.target as InventoryContainer, item: change.item } });
            } else if (change.type === 'remove') {
                inventoryReducer(draft, { type: 'REMOVE_ITEM_FROM_INVENTORY', payload: { owner: change.target as InventoryContainer, item: change.item, quantity: change.item.quantity } });
            }
        });
    }

    if (Array.isArray(result.characterChanges)) {
        result.characterChanges.forEach((change) => {
            if (!change || !change.type || !change.character || !change.character.name) {
                console.warn('Invalid characterChange object:', change);
                return;
            }
            const charData = change.character;
            const maxHp = Number(charData.stats?.maxHp) || 10;
            const maxMp = Number(charData.stats?.maxMp) || 10;
            const maxStamina = Number(charData.stats?.maxStamina) || 10;
            const newChar: Character = {
                name: charData.name,
                description: charData.description || 'A mysterious character.',
                gender: ['male', 'female', 'other'].includes(charData.gender) ? charData.gender : 'other',
                isAI: true,
                portraitStatus: 'pending',
                inventory: Array.isArray(charData.inventory) ? charData.inventory : [],
                stats: {
                    maxHp, maxMp, maxStamina,
                    hp: maxHp, mp: maxMp, stamina: maxStamina,
                    strength: Number(charData.stats?.strength) || 10,
                    agility: Number(charData.stats?.agility) || 10,
                    intelligence: Number(charData.stats?.intelligence) || 10,
                },
            };

            if (change.type === 'add') {
                charactersReducer(draft, { type: 'ADD_CHARACTER', payload: newChar });
            } else if (change.type === 'remove') {
                charactersReducer(draft, { type: 'REMOVE_CHARACTER', payload: { name: change.character.name } });
            }
        });
    }

    if (Array.isArray(result.vehicleChanges)) {
        result.vehicleChanges.forEach((change) => {
            if (!change || !change.type || !change.vehicle || !change.vehicle.id || !change.vehicle.name) return;
            if (change.type === 'add') {
                miscReducer(draft, { type: 'ADD_VEHICLE', payload: { id: change.vehicle.id, name: change.vehicle.name, description: change.vehicle.description || '', inventory: Array.isArray(change.vehicle.inventory) ? change.vehicle.inventory : [] } });
            } else {
                miscReducer(draft, { type: 'REMOVE_VEHICLE', payload: { id: change.vehicle.id } });
            }
        });
    }
    
    if (Array.isArray(result.realEstateChanges)) {
        result.realEstateChanges.forEach((change) => {
            if (!change || !change.type || !change.property || !change.property.id || !change.property.name) return;
            if (change.type === 'add') {
                miscReducer(draft, { type: 'ADD_REAL_ESTATE', payload: { id: change.property.id, name: change.property.name, description: change.property.description || '' } });
            } else {
                miscReducer(draft, { type: 'REMOVE_REAL_ESTATE', payload: { id: change.property.id } });
            }
        });
    }

    if (Array.isArray(result.knownLocations)) {
        result.knownLocations.forEach((loc) => {
            if (loc && loc.id && loc.name) {
                miscReducer(draft, { type: 'ADD_KNOWN_LOCATION', payload: { id: loc.id, name: loc.name, description: loc.description || '' } });
            }
            if (loc.id === 'world-map' && (loc as any).imageUrl) {
                mapReducer(draft, { type: 'SET_MAP_ASSET', payload: { key: 'map-image', url: (loc as any).imageUrl } });
            }
        });
    }
    
    if (Array.isArray(result.tile_changes) && draft.map) {
        result.tile_changes.forEach((change) => {
            if (change && typeof change.x === 'number' && typeof change.y === 'number' && typeof change.tile === 'string') {
                mapReducer(draft, { type: 'UPDATE_MAP_TILE', payload: { x: change.x, y: change.y, tile: change.tile } });
            }
        });
    }

    if (Array.isArray(result.map_object_changes) && draft.map) {
        result.map_object_changes.forEach((change) => {
            if (!change || !change.type || !change.object || !change.object.id) return;
            if (change.type === 'add') {
                 mapReducer(draft, { type: 'ADD_MAP_OBJECT', payload: change.object });
            } else if (change.type === 'remove') {
                mapReducer(draft, { type: 'REMOVE_MAP_OBJECT', payload: { id: change.object.id } });
            }
        });
    }

    if (result.location) miscReducer(draft, { type: 'SET_LOCATION', payload: result.location });
    if (result.gameMode) miscReducer(draft, { type: 'SET_GAME_MODE', payload: result.gameMode });
    if (result.activeEnemies) miscReducer(draft, { type: 'SET_ACTIVE_ENEMIES', payload: Array.isArray(result.activeEnemies) ? result.activeEnemies : [] });
    
    if (Array.isArray(result.resources)) {
        const resourcesMap: Record<string, number> = {};
        result.resources.forEach(resource => {
            if (resource && typeof resource.resourceName === 'string' && typeof resource.quantity === 'number') {
                resourcesMap[resource.resourceName] = resource.quantity;
            }
        });
        miscReducer(draft, { type: 'SET_RESOURCES', payload: resourcesMap });
    } else if (draft.gameMode !== 'simulation') {
        miscReducer(draft, { type: 'SET_RESOURCES', payload: {} });
    }
    
    if (result.newGameLogSummary) {
        gameLogReducer(draft, { type: 'SET_GAME_LOG_SUMMARY', payload: result.newGameLogSummary });
    }

    if (result.suggestedActions) {
        draft.suggestedActions = result.suggestedActions;
    }

    if (draft.initiativeOrder.length > 0 && settings.roundRobinInitiative) { 
         charactersReducer(draft, { type: 'SET_CURRENT_INITIATIVE_INDEX', payload: (draft.currentInitiativeIndex + 1) % draft.initiativeOrder.length });
    }
}


// --- Save File Reconstruction & Cleaning ---

// Helper to check if a value is a non-array object
function isObject(item: any): item is object {
    return item && typeof item === 'object' && !Array.isArray(item);
}

/**
 * Recursively merges the loaded game state with the initial game state to ensure
 * all properties are present, preventing errors from loading older or incomplete save files.
 * @param defaults The base state with all properties (initialGameState).
 * @param specifics The loaded, potentially incomplete, state.
 * @returns A complete and safe GameState object.
 */
function mergeDefaultsDeep<T extends object>(defaults: T, specifics: Partial<T>): T {
    const result: T = { ...specifics } as T; // Start with loaded data

    for (const key in defaults) {
        if (Object.prototype.hasOwnProperty.call(defaults, key)) {
            const defaultVal = defaults[key as keyof T];
            const specificVal = result[key as keyof T];

            if (specificVal === undefined) {
                // Property is missing entirely in loaded data, so use the default.
                result[key as keyof T] = defaultVal;
            } else if (isObject(defaultVal) && isObject(specificVal)) {
                // Property exists in both and is an object, so recurse to fill in nested defaults.
                result[key as keyof T] = mergeDefaultsDeep(defaultVal as object, specificVal as object) as T[keyof T];
            }
            // If property exists in loaded data and is not a plain object (e.g., primitive, array, null),
            // the value from 'specifics' is already in 'result' and is kept as-is.
        }
    }
    return result;
}

/**
 * Takes a potentially incomplete or old game state and merges it with the initial
 * default state to ensure all required fields are present for the current application version.
 * @param loadedState A partial GameState from a save file.
 * @param initialState The complete, default GameState object.
 * @returns A complete and safe-to-use GameState object.
 */
export function reconstructGameState(loadedState: Partial<GameState>, initialState: GameState): GameState {
    return mergeDefaultsDeep(initialState, loadedState);
}

/**
 * Creates a "clean" version of the game state for saving, primarily by removing the asset cache.
 * @param gameState The full, live GameState.
 * @returns A new GameState object suitable for serialization.
 */
export function cleanGameStateForSave(gameState: GameState): GameState {
    return produce(gameState, draft => {
        draft.assetCache = {};
    });
}

/**
 * "Rehydrates" a game state by populating its assetCache from the global codex.
 * This function assumes draft.assetCache may already contain some assets (e.g., from a file load)
 * and only fills in the missing ones.
 * @param gameState A GameState object with a potentially incomplete assetCache.
 * @param codex The global codex containing all known assets.
 * @returns A new GameState object with a populated assetCache, ready for gameplay.
 */
export function rehydrateGameState(gameState: GameState, codex: GlobalCodex): GameState {
    return produce(gameState, draft => {
        draft.assetCache = draft.assetCache || {};

        const sanitizeId = (name: string) => name.toLowerCase().replace(/\s+/g, '-');

        const findAndAddAsset = (key: string | undefined) => {
            if (!key || draft.assetCache[key]) return; // Skip if key is invalid or already in cache

            const findInCodex = (category: keyof GlobalCodex, id: string, urlField: keyof any) => {
                const asset = (codex[category] as any)?.[id];
                if (asset && asset[urlField]) {
                    draft.assetCache[key] = asset[urlField];
                    return true;
                }
                return false;
            };

            const separatorIndex = key.indexOf('-');
            if (separatorIndex !== -1) {
                const type = key.substring(0, separatorIndex);
                const namePart = key.substring(separatorIndex + 1);
                
                // For portraits and icons, the ID is derived from the name part.
                if (type === 'portrait' || type === 'icon') {
                    const lookupId = sanitizeId(namePart);
                    if (type === 'portrait') {
                        if (findInCodex('characters', lookupId, 'imageUrl')) return;
                    } else { // type is 'icon'
                        if (findInCodex('items', lookupId, 'iconUrl')) return;
                        if (findInCodex('blocks', lookupId, 'iconUrl')) return;
                    }
                }
            }

            // Fallback for keys that ARE the ID (e.g., 'world-map', 'cinematic-msg-123')
            // This covers map, location, cinematics, and sfx.
            const allMediaCategories: { cat: keyof GlobalCodex, url: keyof any }[] = [
                { cat: 'images', url: 'url' }, 
                { cat: 'videos', url: 'url' }, 
                { cat: 'audio', url: 'url' }, 
                { cat: 'locations', url: 'imageUrl' }
            ];

            for (const {cat, url} of allMediaCategories) {
                if (findInCodex(cat, key, url)) return;
            }
        };

        // Rehydrate all potential asset keys from the game state
        (draft.characters || []).forEach(char => findAndAddAsset(char.portraitAssetKey));
        
        const allItems = [
            ...(draft.partyStash || []), 
            ...(draft.locationItems || []), 
            ...(draft.characters || []).flatMap(c => c.inventory || []), 
            ...(draft.vehicles || []).flatMap(v => v.inventory || [])
        ];
        allItems.forEach(item => findAndAddAsset(item.iconAssetKey));

        findAndAddAsset(draft.mapAssetKey);
        findAndAddAsset(draft.locationAssetKey);

        (draft.gameLog || []).forEach(msg => {
            findAndAddAsset(msg.cinematic?.assetKey);
            findAndAddAsset(msg.sfx?.assetKey);
        });
    });
}
