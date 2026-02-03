import { produce } from 'immer';
import { GameState, GamePhase, Vehicle, RealEstate, MiscAction } from '../types';

export const miscReducer = (draft: GameState, action: MiscAction) => {
    switch (action.type) {
        case 'SET_GAME_PHASE':
            draft.gamePhase = action.payload;
            break;
        case 'UPDATE_ASSET_CACHE':
            draft.assetCache[action.payload.key] = action.payload.url;
            break;
        case 'ADD_VEHICLE':
            if (!draft.vehicles.some(v => v.id === action.payload.id)) {
                draft.vehicles.push(action.payload);
            }
            break;
        case 'REMOVE_VEHICLE':
            draft.vehicles = draft.vehicles.filter(v => v.id !== action.payload.id);
            break;
        case 'ADD_REAL_ESTATE':
            if (!draft.realEstate.some(r => r.id === action.payload.id)) {
                draft.realEstate.push(action.payload);
            }
            break;
        case 'REMOVE_REAL_ESTATE':
            draft.realEstate = draft.realEstate.filter(r => r.id !== action.payload.id);
            break;
        case 'ADD_KNOWN_LOCATION':
            if (!draft.knownLocations.some(k => k.id === action.payload.id)) {
                draft.knownLocations.push(action.payload);
            }
            break;
        case 'SET_LOCATION':
            draft.location = action.payload;
            break;
        case 'SET_GAME_MODE':
            draft.gameMode = action.payload;
            break;
        case 'SET_ACTIVE_ENEMIES':
            draft.activeEnemies = action.payload;
            break;
        case 'SET_RESOURCES':
            draft.resources = action.payload;
            break;
        case 'SET_FALLBACK_STATUS':
            draft.isFallbackActive = action.payload;
            break;
        case 'RESTART_GAME':
            // Note: Full restart handled in the main reducer composition
            break;
    }
};
