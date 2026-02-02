import { produce } from 'immer';
import { GameState, Character, CharacterStats, CharactersAction } from '../types';

export const charactersReducer = (draft: GameState, action: CharactersAction) => {
    switch (action.type) {
        case 'ADD_CHARACTER':
            if (!draft.characters.some(c => c.name === action.payload.name)) {
                draft.characters.push(action.payload);
                draft.initiativeOrder.push(action.payload.name); // Add to initiative order
            }
            break;
        case 'REMOVE_CHARACTER': {
            const charNameLower = action.payload.name.toLowerCase();
            const index = draft.characters.findIndex(c => c.name.toLowerCase() === charNameLower);
            if (index > -1) {
                draft.characters.splice(index, 1);
                draft.initiativeOrder = draft.initiativeOrder.filter(name => name.toLowerCase() !== charNameLower);
                if (draft.currentInitiativeIndex >= draft.initiativeOrder.length) {
                    draft.currentInitiativeIndex = 0;
                }
            }
            break;
        }
        case 'UPDATE_CHARACTER_PORTRAIT_STATUS': {
            const char = draft.characters.find(c => c.name === action.payload.charName);
            if (char) {
                char.portraitStatus = action.payload.status;
                if (action.payload.assetKey) {
                    char.portraitAssetKey = action.payload.assetKey;
                }
                if (action.payload.imageUrl && action.payload.assetKey) {
                    draft.assetCache[action.payload.assetKey] = action.payload.imageUrl;
                }
            }
            break;
        }
        case 'UPDATE_CHARACTER_STATS': {
            const char = draft.characters.find(c => c.name === action.payload.charName);
            if (char) {
                const statKey = action.payload.stat;
                if (statKey in char.stats && typeof (char.stats as any)[statKey] === 'number') {
                    const maxStatKey = `max${statKey.charAt(0).toUpperCase() + statKey.slice(1)}` as keyof CharacterStats;
                    const maxVal = (char.stats as any)[maxStatKey] ?? Infinity;
                    const currentValue = (char.stats as any)[statKey] as number;
                    const newValue = currentValue + action.payload.change;

                    if (['hp', 'mp', 'stamina', 'm3LogicStress', 'm6SecurityShield'].includes(statKey)) {
                         (char.stats as any)[statKey] = Math.max(0, Math.min(maxVal, newValue));
                    } else { // For other stats like strength, agility, intelligence
                        (char.stats as any)[statKey] = newValue;
                    }
                } else {
                    console.warn(`Invalid stat '${action.payload.stat}' for character '${action.payload.charName}'.`);
                }
            }
            break;
        }
        case 'SET_INITIATIVE_ORDER':
            draft.initiativeOrder = action.payload;
            break;
        case 'SET_CURRENT_INITIATIVE_INDEX':
            draft.currentInitiativeIndex = action.payload;
            break;
    }
};
