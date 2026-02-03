import { produce } from 'immer';
import { GameState, MValMapObject, Item, MapAction } from '../types';
import { findInventory } from '../services/inventoryService';

export const mapReducer = (draft: GameState, action: MapAction) => {
    if (draft.gameStyle !== 'sandbox' && action.type.startsWith('SANDBOX_')) {
        return; // Don't process sandbox actions in narrative mode
    }

    switch (action.type) {
        case 'SET_MAP_IMAGE_URL': // Alias for backwards compatibility during refactor
        case 'SET_MAP_ASSET':
            draft.mapAssetKey = action.payload.key;
            draft.assetCache[action.payload.key] = action.payload.url;
            break;
        case 'SET_LOCATION_IMAGE_URL': // Alias for backwards compatibility during refactor
        case 'SET_LOCATION_ASSET':
            draft.locationAssetKey = action.payload.key;
            draft.assetCache[action.payload.key] = action.payload.url;
            break;
        case 'UPDATE_MAP_TILE':
            if (draft.map && draft.map.tiles[action.payload.y]?.[action.payload.x] !== undefined) {
                draft.map.tiles[action.payload.y][action.payload.x] = action.payload.tile;
            }
            break;
        case 'ADD_MAP_OBJECT':
            if (draft.map && !draft.map.objects.some(o => o.id === action.payload.id)) {
                draft.map.objects.push(action.payload);
            }
            break;
        case 'REMOVE_MAP_OBJECT':
            if (draft.map) {
                draft.map.objects = draft.map.objects.filter(o => o.id !== action.payload.id);
            }
            break;
        case 'SANDBOX_MOVE_PLAYER':
            if (draft.map) {
                draft.map.playerX = action.payload.x;
                draft.map.playerY = action.payload.y;
                draft.map.playerDirection = action.payload.direction;
            }
            break;
        case 'SANDBOX_SET_PLAYER_DIRECTION':
            if (draft.map) {
                draft.map.playerDirection = action.payload;
            }
            break;
        case 'SANDBOX_DIG_TILE':
            if (draft.map) {
                draft.map.tiles[action.payload.y][action.payload.x] = 'air';
                const player = draft.characters.find(c => !c.isAI);
                if (player) {
                    const existingBlock = player.inventory.find(i => i.name.toLowerCase() === action.payload.block.name.toLowerCase());
                    if (existingBlock) {
                        existingBlock.quantity += 1;
                    } else {
                        player.inventory.push({ ...action.payload.block, id: `item-${Date.now()}-${Math.random()}`, quantity: 1 });
                    }
                }
            }
            break;
        case 'SET_MAP_DATA':
            draft.map = action.payload;
            break;
    }
};
